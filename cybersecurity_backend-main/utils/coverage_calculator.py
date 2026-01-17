"""
Vulnerability Coverage Calculator
Calculate coverage percentage for penetration testing phases
"""
from typing import Dict, Any

def calculate_vulnerability_coverage(scan_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate vulnerability coverage based on completed checks.
    
    Returns:
        Dictionary with coverage statistics
    """
    coverage = {
        "total_checks": 0,
        "passed_checks": 0,
        "failed_checks": 0,
        "coverage_percentage": 0.0,
        "categories": {}
    }
    
    # Define expected checks per category
    expected_checks = {
        "passive_recon": {
            "whois": 1,
            "dns": 1,
            "threat_intel": 1,
            "certificates": 1
        },
        "footprinting": {
            "http_headers": 1,
            "security_headers": 4  # X-Frame-Options, X-XSS-Protection, CSP, HSTS
        },
        "network_scanning": {
            "port_scan": 1,
            "service_detection": 1
        },
        "web_scanning": {
            "nikto": 1,
            "gobuster": 1
        },
        "vulnerability_assessment": {
            "openvas": 1,
            "cve_enrichment": 1
        },
        "exploitation": {
            "exploitation_checks": 1
        }
    }
    
    # Check passive reconnaissance
    passive_recon_checks = 0
    passive_recon_total = 4
    if scan_results.get("whois"):
        passive_recon_checks += 1
    if scan_results.get("dns"):
        passive_recon_checks += 1
    if scan_results.get("threat_intel"):
        passive_recon_checks += 1
    if scan_results.get("certificates"):
        passive_recon_checks += 1
    
    coverage["categories"]["passive_recon"] = {
        "total": passive_recon_total,
        "covered": passive_recon_checks,
        "percentage": round((passive_recon_checks / passive_recon_total) * 100, 2)
    }
    
    # Check footprinting
    footprinting_checks = 0
    footprinting_total = 5
    footprinting = scan_results.get("footprinting", {})
    if footprinting.get("server"):
        footprinting_checks += 1
    security_headers = footprinting.get("security_headers", {})
    footprinting_checks += sum(1 for v in security_headers.values() if v)
    
    coverage["categories"]["footprinting"] = {
        "total": footprinting_total,
        "covered": footprinting_checks,
        "percentage": round((footprinting_checks / footprinting_total) * 100, 2)
    }
    
    # Check network scanning
    network_checks = 0
    network_total = 2
    open_ports = scan_results.get("open_ports", [])
    if open_ports:
        network_checks += 1
        # Check if services are detected
        if any(isinstance(p, dict) and p.get("service") for p in open_ports):
            network_checks += 1
    
    coverage["categories"]["network_scanning"] = {
        "total": network_total,
        "covered": network_checks,
        "percentage": round((network_checks / network_total) * 100, 2)
    }
    
    # Check web scanning
    web_checks = 0
    web_total = 2
    if scan_results.get("nikto"):
        web_checks += 1
    if scan_results.get("gobuster"):
        web_checks += 1
    
    coverage["categories"]["web_scanning"] = {
        "total": web_total,
        "covered": web_checks,
        "percentage": round((web_checks / web_total) * 100, 2)
    }
    
    # Check vulnerability assessment
    vuln_checks = 0
    vuln_total = 2
    if scan_results.get("openvas"):
        vuln_checks += 1
    if scan_results.get("vulnerabilities_enriched"):
        vuln_checks += 1
    
    coverage["categories"]["vulnerability_assessment"] = {
        "total": vuln_total,
        "covered": vuln_checks,
        "percentage": round((vuln_checks / vuln_total) * 100, 2)
    }
    
    # Check exploitation
    exploit_checks = 0
    exploit_total = 1
    exploitation = scan_results.get("exploitation", {})
    if exploitation.get("checks_performed", 0) > 0:
        exploit_checks += 1
    
    coverage["categories"]["exploitation"] = {
        "total": exploit_total,
        "covered": exploit_checks,
        "percentage": round((exploit_checks / exploit_total) * 100, 2)
    }
    
    # Calculate totals
    for category in coverage["categories"].values():
        coverage["total_checks"] += category["total"]
        coverage["passed_checks"] += category["covered"]
    
    coverage["failed_checks"] = coverage["total_checks"] - coverage["passed_checks"]
    
    if coverage["total_checks"] > 0:
        coverage["coverage_percentage"] = round(
            (coverage["passed_checks"] / coverage["total_checks"]) * 100, 2
        )
    
    return coverage


def get_coverage_summary(coverage: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of coverage.
    """
    percentage = coverage["coverage_percentage"]
    
    if percentage >= 90:
        return "Excellent - Coverage très complète"
    elif percentage >= 75:
        return "Bon - Coverage satisfaisante"
    elif percentage >= 50:
        return "Moyen - Coverage partielle"
    else:
        return "Faible - Coverage insuffisante"
