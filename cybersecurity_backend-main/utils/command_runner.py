import subprocess
from typing import List

def run_command(command: List[str], timeout: int = 300) -> str:
    """
    Executes a system command and returns the output.
    """
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"
