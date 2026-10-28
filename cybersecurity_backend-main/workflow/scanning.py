import os
import socket
import asyncio
from typing import Dict, Any

import nmap

from utils.command_runner import find_tool

# Configuration (env-overridable)
ALL_PORTS = os.getenv("NMAP_SCAN_ALL_PORTS", "false").lower() in ("1", "true", "yes")
TOP_PORTS = os.getenv("NMAP_TOP_PORTS", "1000")
HOST_TIMEOUT = os.getenv("NMAP_HOST_TIMEOUT", "120s")


async def run_scanning(domain: str, scan_results: Dict[str, Any], log_callback) -> None:
    """
    Step 2: Scanning
    Uses Nmap with service/version detection (-sV) to find open ports and
    identify the software running behind them.

    Port scope (env-configurable):
    - NMAP_SCAN_ALL_PORTS=true -> full 1-65535 range (slow but thorough)
    - default                 -> top 1000 ports (NMAP_TOP_PORTS)
    """
    log_callback("Starting Nmap Scan (service detection enabled)...")

    try:
        # Try to resolve domain to IP first
        try:
            ip_address = socket.gethostbyname(domain)
            log_callback(f"Resolved {domain} to {ip_address}")
            target = ip_address
        except socket.gaierror:
            log_callback(f"Could not resolve {domain}, trying direct scan...")
            target = domain

        port_spec = "-p-" if ALL_PORTS else f"--top-ports {TOP_PORTS}"
        arguments = f"-sV {port_spec} -T4 --host-timeout {HOST_TIMEOUT}"
        log_callback(f"Scanning target: {target} (this may take a few minutes)")

        # Locate the nmap binary (PATH, env override or known install locations)
        nmap_path = find_tool("nmap")
        if nmap_path:
            log_callback(f"Using nmap binary: {nmap_path}")
            search_paths = (nmap_path, "nmap")
        else:
            search_paths = ("nmap", "/usr/bin/nmap", "/usr/local/bin/nmap")

        nm = nmap.PortScanner(nmap_search_path=search_paths)
        # python-nmap is blocking - run in a worker thread to keep the API responsive
        await asyncio.to_thread(nm.scan, target, None, arguments)

        open_ports = []
        all_hosts = nm.all_hosts()

        if all_hosts:
            for host in all_hosts:
                log_callback(f"Scan results for {host}")
                for proto in nm[host].all_protocols():
                    for port in nm[host][proto].keys():
                        info = nm[host][proto][port]
                        state = info.get("state", "unknown")
                        if state != "open":
                            continue

                        service = info.get("name", "unknown")
                        product = info.get("product", "")
                        version = info.get("version", "")

                        entry = {
                            "port": port,
                            "protocol": proto,
                            "state": state,
                            "service": service,
                        }
                        if product:
                            entry["product"] = product
                        if version:
                            entry["version"] = version

                        open_ports.append(entry)

                        label = " ".join(x for x in (service, product, version) if x)
                        log_callback(f"Found open port: {port}/{proto} ({label or 'unknown'})")
        else:
            log_callback("Nmap could not resolve the host or found no ports.")

        scan_results["results"]["open_ports"] = open_ports
        scan_results["results"]["scan_info"] = {
            "target": target,
            "arguments": arguments,
            "all_ports_scan": ALL_PORTS,
        }
        log_callback(f"Scan completed. Found {len(open_ports)} open ports.")

    except Exception as e:
        log_callback(f"Scanning error: {str(e)}")
        scan_results["results"]["open_ports"] = []

    await asyncio.sleep(1)
