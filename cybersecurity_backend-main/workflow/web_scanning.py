import asyncio
import json
import os
import re
import tempfile
import uuid
from typing import Dict, Any, List, Optional

from utils.command_runner import find_tool, run_command_async

# Configuration (env-overridable)
NIKTO_TIMEOUT = int(os.getenv("NIKTO_TIMEOUT", "300"))
GOBUSTER_TIMEOUT = int(os.getenv("GOBUSTER_TIMEOUT", "300"))
GOBUSTER_THREADS = os.getenv("GOBUSTER_THREADS", "20")
GOBUSTER_WORDLIST = os.getenv("GOBUSTER_WORDLIST", "")

# Paths considered sensitive when actually discovered on a target
SENSITIVE_PATH_KEYWORDS = [
    ".git", ".svn", ".env", "backup", "admin", "administrator",
    "phpmyadmin", "wp-config", "id_rsa", ".htaccess", ".htpasswd",
    "config", "database.sql", "dump.sql", "web.config",
    "composer.json", "console", "manager", "server-status", "shell",
]

# Lightweight built-in wordlist, used when no SecLists installation is found
BUILTIN_WORDLIST = [
    "admin", "administrator", "api", "app", "apps", "backup", "bak", "bin",
    "cgi-bin", "composer.json", "config", "console", "dashboard", "database.sql",
    "db", "dev", "Dockerfile", "docker-compose.yml", "dump.sql", ".DS_Store",
    ".env", ".git", ".git/config", ".htaccess", ".htpasswd", "home", "id_rsa",
    "images", "img", "includes", "index.php", "install", "js", "login",
    "logs", "mail", "manager", "media", "new", "old", "package.json", "panel",
    "phpinfo.php", "phpmyadmin", "private", "README.md", "robots.txt",
    "server-status", "setup", "sitemap.xml", "src", "staging", "static",
    "temp", "test", "tmp", "upload", "uploads", "user", "web", "web.config",
    "webmail", "wp-admin", "wp-content", "wp-config.php", "wp-login.php",
    "xmlrpc.php", ".svn", ".svn/entries", "CHANGELOG.md",
]

SEVERITY_HIGH_KEYWORDS = ["rce", "shell", "injection", "traversal", "default account", "backdoor", "remote code"]
SEVERITY_MEDIUM_KEYWORDS = ["outdated", "missing", "cookie", "trace", "clickjack", "enumerate", "default"]


def _get_all_headers(scan_results: Dict[str, Any]) -> Dict[str, str]:
    """Retrieve response headers captured by the footprinting phase.

    Checks the canonical location (results.footprinting.all_headers) with a
    legacy fallback (results.headers).
    """
    results = scan_results.get("results", {})
    footprinting = results.get("footprinting", {})
    if footprinting.get("all_headers"):
        return footprinting["all_headers"]
    return results.get("headers", {})


def _classify_severity(text: str) -> str:
    t = text.lower()
    if any(k in t for k in SEVERITY_HIGH_KEYWORDS):
        return "high"
    if any(k in t for k in SEVERITY_MEDIUM_KEYWORDS):
        return "medium"
    return "info"


# ============== NIKTO ==============

def _parse_nikto_json(out_file: str) -> List[Dict[str, str]]:
    """Parse Nikto JSON output (-Format json) into normalized findings.

    Nikto 2.5+ writes a list of host reports, each containing a
    'vulnerabilities' list of dicts with an 'msg' field. Older versions
    wrote a single report object.
    """
    try:
        with open(out_file, "r", encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
    except Exception:
        return []

    reports = data if isinstance(data, list) else [data]
    findings = []
    for report in reports:
        if not isinstance(report, dict):
            continue
        for vuln in report.get("vulnerabilities") or []:
            if not isinstance(vuln, dict):
                continue
            text = (
                vuln.get("msg")
                or vuln.get("outputline")
                or vuln.get("items")
                or vuln.get("hints")
                or vuln.get("id")
                or ""
            )
            if isinstance(text, list):
                text = "; ".join(str(t) for t in text)
            text = str(text).strip()
            if not text:
                continue
            findings.append({"severity": _classify_severity(text), "issue": text})
    return findings


def _nikto_heuristics(scan_results: Dict[str, Any], log_callback) -> List[Dict[str, str]]:
    """Built-in header-based checks used when the Nikto binary is unavailable.

    Deliberately avoids duplicating footprinting's own 4 security-header
    checks; focuses on cookies, extra headers, methods and disclosure.
    """
    headers = _get_all_headers(scan_results)
    findings = []

    server = headers.get("Server", "")
    if server and server != "Unknown" and any(c.isdigit() for c in server):
        findings.append({"severity": "info", "issue": f"Server leaks version information: {server}"})

    powered = headers.get("X-Powered-By", "")
    if powered:
        findings.append({"severity": "info", "issue": f"Uncommon header 'x-powered-by' found: {powered}"})

    if "X-Content-Type-Options" not in headers:
        findings.append({"severity": "medium", "issue": "Missing X-Content-Type-Options header (MIME-sniffing possible)"})
        scan_results["vulns"] += 1

    if "Referrer-Policy" not in headers:
        findings.append({"severity": "info", "issue": "Missing Referrer-Policy header"})

    cookie = headers.get("Set-Cookie", "")
    if cookie:
        missing_flags = []
        if "httponly" not in cookie.lower():
            missing_flags.append("HttpOnly")
        if "secure" not in cookie.lower():
            missing_flags.append("Secure")
        if missing_flags:
            findings.append({
                "severity": "medium",
                "issue": f"Session cookie missing flags: {', '.join(missing_flags)}"
            })
            scan_results["vulns"] += 1

    allow = headers.get("Allow", "")
    if "TRACE" in allow.upper():
        findings.append({"severity": "high", "issue": "HTTP TRACE method enabled (Cross-Site Tracing)"})
        scan_results["vulns"] += 1

    for f in findings:
        log_callback(f"Nikto: Found - {f['issue']}")
    return findings


async def run_nikto(target_url: str, scan_results: Dict[str, Any], log_callback) -> None:
    """
    Run Nikto web server scanner.
    Executes the real nikto binary when available (-Format json); otherwise
    falls back to built-in heuristic checks. Never fabricates findings.
    """
    log_callback(f"Starting Nikto web vulnerability scan on {target_url}...")

    server_header = _get_all_headers(scan_results).get("Server", "")
    findings: List[Dict[str, str]] = []
    mode = "heuristic"

    nikto_path = find_tool("nikto", "nikto.pl")
    if nikto_path:
        out_file = os.path.join(tempfile.gettempdir(), f"nikto_{uuid.uuid4().hex}.json")
        try:
            # Perl scripts (.pl) must be executed through the perl interpreter on Windows
            if nikto_path.lower().endswith(".pl"):
                perl_path = find_tool("perl")
                if not perl_path:
                    raise RuntimeError("nikto.pl found but Perl is not installed")
                cmd = [perl_path, nikto_path, "-h", target_url]
            else:
                cmd = [nikto_path, "-h", target_url]
            cmd += ["-o", out_file, "-Format", "json", "-nointeractive", "-timeout", "10"]
            log_callback(f"Nikto binary found ({nikto_path}) - running real scan (may take several minutes)...")
            rc, stdout, stderr = await run_command_async(cmd, timeout=NIKTO_TIMEOUT)

            if os.path.exists(out_file):
                findings = _parse_nikto_json(out_file)

            if findings:
                mode = "real"
                for f in findings:
                    log_callback(f"Nikto: [{f['severity'].upper()}] {f['issue']}")
            else:
                detail = stderr.strip()[:200] if stderr else "no JSON output produced"
                log_callback(f"Nikto: real scan produced no findings (exit code {rc}: {detail})")
        except Exception as e:
            log_callback(f"Nikto real scan failed ({e}) - falling back to built-in heuristics")
        finally:
            if os.path.exists(out_file):
                try:
                    os.remove(out_file)
                except OSError:
                    pass

    if mode == "heuristic":
        log_callback("Nikto binary not available or scan failed - running built-in heuristic checks")
        findings = _nikto_heuristics(scan_results, log_callback)

    scan_results["results"]["nikto"] = {
        "target": target_url,
        "server": server_header,
        "mode": mode,
        "issues_count": len(findings),
        "findings": [f"{f['severity'].upper()}: {f['issue']}" for f in findings],
    }
    log_callback(f"Nikto scan completed ({mode} mode). Found {len(findings)} issues.")


# ============== GOBUSTER ==============

def _resolve_wordlist(log_callback) -> Optional[str]:
    """Locate a directory wordlist: env var -> SecLists/dirb paths -> built-in list."""
    candidates = []
    if GOBUSTER_WORDLIST:
        candidates.append(GOBUSTER_WORDLIST)
    candidates += [
        "/usr/share/wordlists/dirb/common.txt",
        "/usr/share/wordlists/dirbuster/directory-list-2.3-small.txt",
        "/usr/local/share/wordlists/dirb/common.txt",
        r"C:\wordlists\dirb\common.txt",
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate

    # Write the built-in list to a temp file (gobuster entries are relative paths)
    wordlist_file = os.path.join(tempfile.gettempdir(), f"wordlist_{uuid.uuid4().hex}.txt")
    try:
        with open(wordlist_file, "w", encoding="utf-8") as fh:
            fh.write("\n".join(p.lstrip("/") for p in BUILTIN_WORDLIST))
        return wordlist_file
    except Exception as e:
        log_callback(f"Gobuster: could not create wordlist file ({e})")
        return None


def _parse_gobuster_output(stdout: str) -> List[Dict[str, Any]]:
    """Parse gobuster dir output lines.

    Handles both formats:
      new: /admin [Status: 403, Size: 1024, Words: 5, Lines: 2]
      old: /admin (Status: 403) [Size: 1024]
    """
    paths = []
    for line in stdout.splitlines():
        line = line.strip()
        status_match = re.search(r"Status:\s*(\d{3})", line)
        if not line or not status_match:
            continue
        path = line.split()[0] if line.split() else ""
        if not path:
            continue
        size_match = re.search(r"Size:\s*(\d+)", line)
        paths.append({
            "path": path if path.startswith("/") else f"/{path}",
            "status": int(status_match.group(1)),
            "size": int(size_match.group(1)) if size_match else 0,
        })
    return paths


async def run_gobuster(target_url: str, scan_results: Dict[str, Any], log_callback) -> None:
    """
    Run Gobuster directory/file bruteforcing.
    Executes the real gobuster binary when available; otherwise skips the
    scan entirely (no simulated data). Only real discoveries are reported.
    """
    log_callback(f"Starting Gobuster directory enumeration on {target_url}...")

    paths: List[Dict[str, Any]] = []
    mode = "skipped"

    gobuster_path = find_tool("gobuster")
    if not gobuster_path:
        log_callback("Gobuster binary not found - directory enumeration skipped (install gobuster to enable)")
    else:
        wordlist = _resolve_wordlist(log_callback)
        if not wordlist:
            log_callback("Gobuster: no wordlist available - directory enumeration skipped")
        else:
            log_callback(
                f"Gobuster binary found ({gobuster_path}) - running real scan "
                f"with wordlist: {os.path.basename(wordlist)}"
            )
            base_cmd = [
                gobuster_path, "dir", "-u", target_url,
                "-w", wordlist, "-t", GOBUSTER_THREADS,
                "-q", "--no-color",
            ]
            # Newer gobuster uses -b; older versions use --status-codes-blacklist
            rc, stdout, stderr = await run_command_async(
                base_cmd + ["-b", "404"], timeout=GOBUSTER_TIMEOUT
            )
            if rc != 0 and ("flag provided" in stderr or "unknown shorthand flag" in stderr):
                rc, stdout, stderr = await run_command_async(
                    base_cmd + ["--status-codes-blacklist", "404"], timeout=GOBUSTER_TIMEOUT
                )

            paths = _parse_gobuster_output(stdout)
            mode = "real"
            if not paths:
                detail = stderr.strip()[:200] if stderr else "no matches found"
                log_callback(f"Gobuster: no paths discovered (exit code {rc}: {detail})")

            try:
                if wordlist.startswith(tempfile.gettempdir()):
                    os.remove(wordlist)
            except OSError:
                pass

    # Assess discovered paths for sensitive content
    for p in paths:
        status = p["status"]
        sensitive = any(k in p["path"].lower() for k in SENSITIVE_PATH_KEYWORDS)
        if sensitive and status in (200, 403):
            p["sensitive"] = True
            log_callback(f"Gobuster: [SENSITIVE] Found {p['path']} (Status: {status})")
            scan_results["vulns"] += 1
        else:
            log_callback(f"Gobuster: Found path: {p['path']} (Status: {status})")

    scan_results["results"]["gobuster"] = {
        "target": target_url,
        "mode": mode,
        "paths": paths,
    }
    log_callback(f"Gobuster completed ({mode} mode). Discovered {len(paths)} paths.")
