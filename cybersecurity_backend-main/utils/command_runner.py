"""Command execution utilities for security tool integration.

Provides tool discovery (PATH + known install locations + env overrides)
and safe subprocess execution. All workflow integrations (nikto, gobuster)
must run binaries through this module so timeouts and errors are handled
uniformly.
"""

import os
import shutil
import subprocess
import asyncio
from typing import List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

# Fallback install locations checked when the binary is not on PATH
_KNOWN_LOCATIONS = {
    "nmap": [
        r"C:\Program Files (x86)\Nmap\nmap.exe",
        r"C:\Program Files\Nmap\nmap.exe",
        "/usr/bin/nmap",
        "/usr/local/bin/nmap",
    ],
    "nikto": [
        "/usr/bin/nikto",
        "/usr/local/bin/nikto",
        "/usr/share/nikto/nikto.pl",
    ],
    "gobuster": [
        "/usr/bin/gobuster",
        "/usr/local/bin/gobuster",
        r"C:\tools\gobuster\gobuster.exe",
    ],
    "perl": [
        r"C:\Strawberry\perl\bin\perl.exe",
        "/usr/bin/perl",
    ],
}


def find_tool(*names: str) -> Optional[str]:
    """Locate a tool binary.

    Resolution order:
    1. <NAME>_PATH environment variable (e.g. NIKTO_PATH, GOBUSTER_PATH)
    2. System PATH (shutil.which)
    3. Known install locations

    Returns the binary path or None if not found.
    """
    for name in names:
        env_path = os.getenv(f"{name.split('.')[0].upper()}_PATH", "")
        if env_path and os.path.isfile(env_path):
            return env_path

        found = shutil.which(name)
        if found:
            return found

        for location in _KNOWN_LOCATIONS.get(name, []):
            if os.path.isfile(location):
                return location

    return None


def run_command(command: List[str], timeout: int = 300) -> Tuple[int, str, str]:
    """Execute a system command synchronously.

    Returns (returncode, stdout, stderr). Never raises - all failures are
    reported through the returncode/stderr so callers can degrade gracefully.
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "Error: Command timed out"
    except FileNotFoundError:
        return -1, "", "Error: Command not found"
    except Exception as e:
        return -1, "", f"Error: {str(e)}"


async def run_command_async(command: List[str], timeout: int = 300) -> Tuple[int, str, str]:
    """Execute a system command in a worker thread (async-safe)."""
    return await asyncio.to_thread(run_command, command, timeout)
