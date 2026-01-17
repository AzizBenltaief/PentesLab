import nmap
import asyncio
import socket
from typing import Dict, Any

async def run_scanning(domain: str, scan_results: Dict[str, Any], log_callback) -> None:
    """
    Step 2: Scanning
    Uses Nmap to find open ports.
    """
    log_callback("Starting Nmap Scan...")
    
    try:
        # Try to resolve domain to IP first
        try:
            ip_address = socket.gethostbyname(domain)
            log_callback(f"Resolved {domain} to {ip_address}")
            target = ip_address
        except socket.gaierror:
            log_callback(f"Could not resolve {domain}, trying direct scan...")
            target = domain
        
        nm = nmap.PortScanner()
        # Quick scan of common ports to keep it fast
        # -F: Fast mode - Scan fewer ports than the default scan
        # -T4: Aggressive timing template
        # --host-timeout: Don't wait too long for unresponsive hosts
        log_callback(f"Scanning target: {target}")
        nm.scan(target, arguments='-F -T4 --host-timeout 30s')
        
        open_ports = []
        all_hosts = nm.all_hosts()
        
        if all_hosts:
            for host in all_hosts:
                log_callback(f"Scanning results for {host}")
                for proto in nm[host].all_protocols():
                    ports = nm[host][proto].keys()
                    for port in ports:
                        state = nm[host][proto][port]['state']
                        if state == 'open':
                            service = nm[host][proto][port].get('name', 'unknown')
                            open_ports.append({
                                "port": port,
                                "protocol": proto,
                                "state": state,
                                "service": service
                            })
                            log_callback(f"Found open port: {port}/{proto} ({service})")
        else:
            log_callback("Nmap could not resolve the host or found no ports.")
            
        scan_results["results"]["open_ports"] = open_ports
        log_callback(f"Scan completed. Found {len(open_ports)} open ports.")
        
    except Exception as e:
        log_callback(f"Scanning error: {str(e)}")
        scan_results["results"]["open_ports"] = []
        
    await asyncio.sleep(2)
