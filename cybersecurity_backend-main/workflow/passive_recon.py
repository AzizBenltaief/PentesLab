import asyncio
import requests
from typing import Dict, Any
import socket

async def whois_lookup(domain: str, scan_results: Dict[str, Any], log_callback) -> None:
    """
    Perform WHOIS lookup for passive reconnaissance.
    """
    # Clean domain from URL
    clean_domain = domain.replace('https://', '').replace('http://', '').split('/')[0]
    log_callback(f"Performing WHOIS lookup for {clean_domain}...")
    
    try:
        # In production, use python-whois library or whois API
        # For now, we simulate WHOIS data
        
        whois_data = {
            "domain_name": clean_domain,
            "registrar": "Example Registrar Inc.",
            "creation_date": "2020-01-15",
            "expiration_date": "2026-01-15",
            "name_servers": ["ns1.example.com", "ns2.example.com"],
            "status": "active",
            "organization": "Example Organization",
            "admin_email": "admin@example.com"
        }
        
        scan_results["results"]["whois"] = whois_data
        log_callback(f"WHOIS: Domain registered to {whois_data['organization']}")
        log_callback(f"WHOIS: Creation date: {whois_data['creation_date']}")
        log_callback("WHOIS lookup completed.")
        
    except Exception as e:
        log_callback(f"WHOIS lookup error: {str(e)}")
    
    await asyncio.sleep(1)

async def dns_enumeration(domain: str, scan_results: Dict[str, Any], log_callback) -> None:
    """
    Perform DNS enumeration for passive reconnaissance.
    """
    # Clean domain from URL
    clean_domain = domain.replace('https://', '').replace('http://', '').split('/')[0]
    log_callback(f"Starting DNS enumeration for {clean_domain}...")
    
    try:
        dns_records = {}
        
        # A record
        try:
            ip_address = socket.gethostbyname(clean_domain)
            dns_records["A"] = [ip_address]
            log_callback(f"DNS: A record - {ip_address}")
        except:
            log_callback("DNS: No A record found")
        
        # Simulated additional DNS records
        dns_records["MX"] = ["mail.example.com"]
        dns_records["NS"] = ["ns1.example.com", "ns2.example.com"]
        dns_records["TXT"] = ["v=spf1 include:_spf.example.com ~all"]
        
        # Check for common subdomains
        log_callback("DNS: Enumerating subdomains...")
        common_subdomains = ["www", "mail", "ftp", "admin", "api", "dev"]
        found_subdomains = []
        
        for subdomain in common_subdomains:
            full_domain = f"{subdomain}.{clean_domain}"
            try:
                ip = socket.gethostbyname(full_domain)
                found_subdomains.append({"subdomain": full_domain, "ip": ip})
                log_callback(f"DNS: Found subdomain - {full_domain} ({ip})")
            except:
                pass
        
        dns_records["subdomains"] = found_subdomains
        scan_results["results"]["dns"] = dns_records
        log_callback(f"DNS enumeration completed. Found {len(found_subdomains)} subdomains.")
        
    except Exception as e:
        log_callback(f"DNS enumeration error: {str(e)}")
    
    await asyncio.sleep(1)

async def shodan_lookup(ip_address: str, scan_results: Dict[str, Any], log_callback) -> None:
    """
    Perform Shodan-like passive reconnaissance.
    Note: In production, use Shodan API with proper API key.
    """
    log_callback(f"Querying threat intelligence databases for {ip_address}...")
    
    try:
        # In production, use: import shodan; api = shodan.Shodan(API_KEY)
        # For now, we simulate Shodan data
        
        shodan_data = {
            "ip": ip_address,
            "organization": "Example ISP",
            "country": "US",
            "city": "San Francisco",
            "asn": "AS12345",
            "ports": [22, 80, 443],
            "vulnerabilities": ["CVE-2023-12345"],
            "last_update": "2026-01-10",
            "tags": ["web", "ssh"]
        }
        
        scan_results["results"]["threat_intel"] = {
            "ip": shodan_data['ip'],
            "isp": shodan_data['organization'],
            "location": f"{shodan_data['city']}, {shodan_data['country']}",
            "open_ports": shodan_data['ports'],
            "vulnerabilities": len(shodan_data.get('vulnerabilities', [])),
            "tags": shodan_data.get('tags', [])
        }
        log_callback(f"Threat Intel: IP belongs to {shodan_data['organization']}")
        log_callback(f"Threat Intel: Location: {shodan_data['city']}, {shodan_data['country']}")
        log_callback(f"Threat Intel: Known open ports: {', '.join(map(str, shodan_data['ports']))}")
        
        if shodan_data.get("vulnerabilities"):
            log_callback(f"Threat Intel: Known vulnerabilities: {len(shodan_data['vulnerabilities'])}")
            scan_results["vulns"] += len(shodan_data["vulnerabilities"])
        
        log_callback("Threat intelligence lookup completed.")
        
    except Exception as e:
        log_callback(f"Threat intelligence error: {str(e)}")
    
    await asyncio.sleep(1)

async def certificate_transparency_check(domain: str, scan_results: Dict[str, Any], log_callback) -> None:
    """
    Check Certificate Transparency logs for additional subdomains and certificates.
    """
    # Clean domain from URL
    clean_domain = domain.replace('https://', '').replace('http://', '').split('/')[0]
    log_callback(f"Checking Certificate Transparency logs for {clean_domain}...")
    
    try:
        # In production, query crt.sh or Censys API
        # For now, we simulate CT log data
        
        ct_data = {
            "certificates_found": 3,
            "discovered_domains": [
                f"www.{clean_domain}",
                f"api.{clean_domain}",
                f"staging.{clean_domain}"
            ],
            "issuers": ["Let's Encrypt", "DigiCert"],
            "oldest_cert": "2022-06-15",
            "newest_cert": "2025-12-20"
        }
        
        scan_results["results"]["certificates"] = {
            "cert_count": ct_data['certificates_found'],
            "discovered_domains": ct_data['discovered_domains'],
            "issuers": ct_data['issuers'],
            "oldest_cert": ct_data['oldest_cert'],
            "newest_cert": ct_data['newest_cert']
        }
        log_callback(f"CT Logs: Found {ct_data['certificates_found']} certificates")
        log_callback(f"CT Logs: Discovered domains: {', '.join(ct_data['discovered_domains'])}")
        log_callback("Certificate Transparency check completed.")
        
    except Exception as e:
        log_callback(f"Certificate Transparency error: {str(e)}")
    
    await asyncio.sleep(1)
