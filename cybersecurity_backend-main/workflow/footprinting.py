import requests
import asyncio
from typing import Dict, Any

async def run_footprinting(target_url: str, scan_results: Dict[str, Any], log_callback) -> None:
    """
    Step 1: Footprinting
    Analyzes HTTP headers and basic server info.
    """
    log_callback(f"Starting Footprinting on {target_url}...")
    
    try:
        # Run in a thread executor if requests is blocking, but for this simple check it's okay-ish 
        # or we can use aiohttp. For now, keeping requests but wrapping in try/except block.
        # In a real async app, use aiohttp.
        
        response = requests.get(target_url, timeout=10)
        headers = response.headers
        server = headers.get("Server", "Unknown")
        
        log_callback(f"Detected Server: {server}")
        
        # Security Header Checks
        missing_headers = []
        security_headers_check = {
            "X-Frame-Options": "X-Frame-Options" in headers,
            "X-XSS-Protection": "X-XSS-Protection" in headers,
            "Content-Security-Policy": "Content-Security-Policy" in headers,
            "Strict-Transport-Security": "Strict-Transport-Security" in headers
        }
        
        for header, present in security_headers_check.items():
            if not present:
                missing_headers.append(header)
        
        if missing_headers:
            scan_results["vulns"] += len(missing_headers)
            for mh in missing_headers:
                log_callback(f"Vulnerability: Missing {mh} header")
        
        # Store structured footprinting data
        scan_results["results"]["footprinting"] = {
            "server": server,
            "technologies": [server],
            "security_headers": security_headers_check,
            "all_headers": dict(headers)
        }
        # Legacy alias consumed by openvas_integration and web_scanning heuristics
        scan_results["results"]["headers"] = dict(headers)
                
    except Exception as e:
        log_callback(f"Footprinting error: {str(e)}")
    
    await asyncio.sleep(2) # Simulate deeper analysis
