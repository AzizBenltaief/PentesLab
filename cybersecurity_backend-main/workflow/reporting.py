import asyncio
from datetime import datetime
from typing import Dict, Any


async def run_reporting(scan_results: Dict[str, Any], target: str = "") -> str:
    """
    Generate the pentest report: AI-generated when the Groq agent is
    available, deterministic template otherwise (graceful fallback).
    Returns a comprehensive markdown-formatted report.
    """
    from agent.report_agent import generate_ai_report

    fallback = generate_professional_report(scan_results)
    return await generate_ai_report(scan_results, target=target, fallback_report=fallback)


def generate_professional_report(scan_results: Dict[str, Any]) -> str:
    """Generate a professional penetration testing report using templates."""
    
    # Extract all scan data
    whois = scan_results.get("whois", {})
    dns = scan_results.get("dns", {})
    threat_intel = scan_results.get("threat_intel", {})
    certificates = scan_results.get("certificates", {})
    footprinting = scan_results.get("footprinting", {})
    open_ports = scan_results.get("open_ports", [])
    nikto = scan_results.get("nikto", {})
    gobuster = scan_results.get("gobuster", {})
    openvas = scan_results.get("openvas", {})
    vulnerabilities = scan_results.get("vulnerabilities_enriched", [])
    exploitation = scan_results.get("exploitation", {})
    
    # Calculate statistics
    domain = whois.get('domain_name', 'Unknown Target')
    org = whois.get('organization', 'Unknown Organization')
    vuln_count = len(vulnerabilities)
    port_count = len(open_ports)
    
    critical_vulns = sum(1 for v in vulnerabilities if v.get('cvss', 0) >= 9.0)
    high_vulns = sum(1 for v in vulnerabilities if 7.0 <= v.get('cvss', 0) < 9.0)
    medium_vulns = sum(1 for v in vulnerabilities if 4.0 <= v.get('cvss', 0) < 7.0)
    low_vulns = sum(1 for v in vulnerabilities if v.get('cvss', 0) < 4.0)
    
    overall_risk = "CRITICAL" if critical_vulns > 0 else "HIGH" if high_vulns > 0 else "MEDIUM" if medium_vulns > 0 else "LOW"
    
    # Generate report
    report = f"""# Penetration Testing Report

## Executive Summary

This report presents the findings from a comprehensive penetration test conducted on **{domain}** (owned by {org}). The assessment employed industry-standard methodologies including OWASP Testing Guide and PTES (Penetration Testing Execution Standard).

### Overall Risk Assessment: **{overall_risk}**

**Key Findings:**
- **{vuln_count}** security vulnerabilities identified
  - {critical_vulns} Critical | {high_vulns} High | {medium_vulns} Medium | {low_vulns} Low
- **{port_count}** open network ports discovered
- **{nikto.get('issues_count', 0)}** web application issues detected
- **{len(gobuster.get('paths', []))}** web paths enumerated
- **{len(certificates.get('discovered_domains', []))}** subdomains discovered

---

## 1. Reconnaissance Phase

### 1.1 WHOIS Information
- **Domain:** {whois.get('domain_name', 'N/A')}
- **Registrar:** {whois.get('registrar', 'N/A')}
- **Organization:** {whois.get('organization', 'N/A')}
- **Creation Date:** {whois.get('creation_date', 'N/A')}
- **Expiration Date:** {whois.get('expiration_date', 'N/A')}
- **Status:** {whois.get('status', 'N/A')}

### 1.2 DNS Infrastructure
- **A Records:** {', '.join(dns.get('A', ['None']))}
- **MX Records:** {', '.join(dns.get('MX', ['None']))}
- **NS Records:** {', '.join(dns.get('NS', ['None']))}
- **TXT Records:** {len(dns.get('TXT', []))} records found

**Security Implications:** DNS configuration reveals infrastructure layout and potential targets for attacks.

### 1.3 Threat Intelligence
- **IP Address:** {threat_intel.get('ip', 'N/A')}
- **ISP/Provider:** {threat_intel.get('isp', 'N/A')}
- **Geolocation:** {threat_intel.get('location', 'N/A')}
- **Known Open Ports:** {', '.join(map(str, threat_intel.get('open_ports', [])))}
- **Known Vulnerabilities:** {threat_intel.get('vulnerabilities', 0)}

### 1.4 Certificate Transparency Logs
- **SSL Certificates Found:** {certificates.get('cert_count', 0)}
- **Certificate Issuers:** {', '.join(certificates.get('issuers', []))}
- **Discovered Subdomains:**
"""
    
    for subdomain in certificates.get('discovered_domains', [])[:10]:
        report += f"  - {subdomain}\n"
    
    report += f"""
**Risk:** Certificate transparency logs expose subdomains that may not be properly secured.

---

## 2. Network Security Assessment

### 2.1 Open Ports Analysis
**Total Open Ports:** {port_count}

"""
    
    # Group ports by risk level
    high_risk_ports = [21, 23, 3306, 3389, 5900]
    critical_ports = []
    
    for port in open_ports[:20]:  # Show first 20
        port_num = port.get('port') if isinstance(port, dict) else port
        service = port.get('service', 'unknown') if isinstance(port, dict) else 'unknown'
        state = port.get('state', 'open') if isinstance(port, dict) else 'open'
        
        risk_indicator = "🔴" if port_num in high_risk_ports else "🟡"
        report += f"{risk_indicator} **Port {port_num}** ({service}) - {state}\n"
        
        if port_num in high_risk_ports:
            critical_ports.append((port_num, service))
    
    if port_count > 20:
        report += f"\n*... and {port_count - 20} additional ports*\n"
    
    if critical_ports:
        report += "\n**High-Risk Ports Detected:**\n"
        for port, service in critical_ports:
            report += f"- Port {port}/{service}: {get_port_risk_description(port)}\n"
    
    report += """
**Recommendation:** Implement network segmentation, close unnecessary ports, and use firewall rules to restrict access.

### 2.2 Service Fingerprinting
"""
    
    report += f"- **Web Server:** {footprinting.get('server', 'Not detected')}\n"
    report += f"- **Technologies:** {', '.join(footprinting.get('technologies', ['None detected']))}\n"
    
    report += """

### 2.3 Security Headers Analysis
"""
    
    security_headers = footprinting.get('security_headers', {})
    missing_headers = [h for h, present in security_headers.items() if not present]
    
    if missing_headers:
        report += f"**⚠️ Missing Security Headers:** {len(missing_headers)}\n\n"
        for header in missing_headers:
            report += f"- ❌ **{header}**\n  - {get_header_description(header)}\n"
    else:
        report += "✅ All critical security headers are present.\n"
    
    report += """

---

## 3. Web Application Security

### 3.1 Nikto Vulnerability Scan
"""
    
    report += f"- **Target:** {nikto.get('target', 'N/A')}\n"
    report += f"- **Server:** {nikto.get('server', 'Unknown')}\n"
    report += f"- **Issues Found:** {nikto.get('issues_count', 0)}\n\n"
    
    if nikto.get('findings'):
        report += "**Findings:**\n"
        for finding in nikto.get('findings', [])[:10]:
            report += f"- {finding}\n"
    else:
        report += "✅ No critical web vulnerabilities detected by Nikto.\n"
    
    report += """

### 3.2 Directory Enumeration (Gobuster)
"""
    
    paths = gobuster.get('paths', [])
    report += f"**Total Paths Discovered:** {len(paths)}\n\n"
    
    if paths:
        critical_paths = [p for p in paths if p.get('status') in [200, 403] and any(keyword in p.get('path', '') for keyword in ['/admin', '/backup', '/.git', '/config'])]
        
        if critical_paths:
            report += "**🔴 Critical Paths:**\n"
            for path in critical_paths[:5]:
                report += f"- `{path.get('path')}` (Status: {path.get('status')}, Size: {path.get('size')})\n"
                report += f"  - Risk: {get_path_risk_description(path.get('path'))}\n"
        
        report += "\n**Other Discovered Paths:**\n"
        for path in [p for p in paths if p not in critical_paths][:10]:
            report += f"- `{path.get('path')}` (Status: {path.get('status')})\n"
    
    report += """

---

## 4. Vulnerability Assessment (OpenVAS)

"""
    
    if vulnerabilities:
        report += f"**Total Vulnerabilities:** {len(vulnerabilities)}\n"
        report += f"**Average Risk Score:** {openvas.get('risk_score', 0):.2f}/10\n\n"
        
        # Show critical and high vulnerabilities
        critical_high = [v for v in vulnerabilities if v.get('cvss', 0) >= 7.0]
        
        if critical_high:
            report += "### 🔴 Critical & High Severity Vulnerabilities\n\n"
            
            for vuln in critical_high:
                severity_emoji = "🔴" if vuln.get('cvss', 0) >= 9.0 else "🟠"
                report += f"{severity_emoji} **{vuln.get('nvt', vuln.get('name', 'Unknown Vulnerability'))}**\n"
                report += f"- **CVSS Score:** {vuln.get('cvss', 'N/A')}\n"
                report += f"- **Severity:** {vuln.get('severity', 'N/A')}\n"
                report += f"- **Port:** {vuln.get('port', 'N/A')}\n"
                report += f"- **Description:** {vuln.get('description', 'No description')[:200]}...\n"
                report += f"- **Solution:** {vuln.get('solution', 'Update software to latest version')}\n\n"
        
        # Show medium and low
        medium_low = [v for v in vulnerabilities if v.get('cvss', 0) < 7.0]
        if medium_low:
            report += f"\n### Medium & Low Severity ({len(medium_low)} findings)\n"
            for vuln in medium_low[:5]:
                report += f"- {vuln.get('nvt', vuln.get('name', 'Unknown'))} (CVSS: {vuln.get('cvss', 'N/A')})\n"
    else:
        report += "✅ No vulnerabilities detected by OpenVAS scanner.\n"
    
    report += """

---

## 5. Exploitation Analysis

"""
    
    report += f"**Checks Performed:** {exploitation.get('checks_performed', 0)}\n\n"
    
    findings = exploitation.get('findings', [])
    if findings:
        report += "**Exploitation Test Results:**\n\n"
        for finding in findings:
            status = finding.get('status', 'unknown')
            icon = "🔴" if status == 'vulnerable' else "✅" if status == 'completed' else "⚪"
            
            report += f"{icon} **{finding.get('check', 'Unknown Test')}**\n"
            report += f"- Status: {status.upper()}\n"
            if finding.get('findings'):
                report += f"- Details: {finding.get('findings')}\n"
            if finding.get('severity'):
                report += f"- Severity: {finding.get('severity')}\n"
            report += "\n"
    else:
        report += "No exploitation attempts were made during this assessment.\n"
    
    report += """

---

## 6. Risk Analysis & Prioritization

### Vulnerability Distribution
"""
    
    report += f"- **Critical (CVSS 9.0-10.0):** {critical_vulns} vulnerabilities\n"
    report += f"- **High (CVSS 7.0-8.9):** {high_vulns} vulnerabilities\n"
    report += f"- **Medium (CVSS 4.0-6.9):** {medium_vulns} vulnerabilities\n"
    report += f"- **Low (CVSS 0.1-3.9):** {low_vulns} vulnerabilities\n\n"
    
    report += """### Attack Surface Analysis
"""
    
    report += f"- **Network Attack Surface:** {port_count} open ports\n"
    report += f"- **Web Attack Surface:** {len(paths)} accessible paths\n"
    report += f"- **Missing Security Controls:** {len(missing_headers)} security headers\n"
    report += f"- **Exposed Services:** {len([p for p in open_ports if isinstance(p, dict)])} identified services\n\n"
    
    report += """

---

## 7. Recommendations

### 🔴 Critical Priority (Immediate Action Required)
"""
    
    recommendations = []
    
    if critical_vulns > 0:
        recommendations.append("1. **Patch Critical Vulnerabilities:** Immediately address all CRITICAL severity vulnerabilities to prevent exploitation")
    
    if any(p.get('port') if isinstance(p, dict) else p in [21, 23, 3389] for p in open_ports):
        recommendations.append("2. **Secure High-Risk Services:** FTP, Telnet, and RDP detected - implement strong authentication or disable")
    
    if 'X-Frame-Options' in missing_headers:
        recommendations.append("3. **Implement Security Headers:** Add missing security headers to prevent common web attacks")
    
    if any(keyword in p.get('path', '') for p in paths for keyword in ['/admin', '/.git', '/backup']):
        recommendations.append("4. **Restrict Sensitive Paths:** Secure or remove exposed administrative interfaces and backup files")
    
    for i, rec in enumerate(recommendations, 1):
        report += f"{rec}\n"
    
    report += """

### 🟡 High Priority (Within 30 Days)
1. **Implement Network Segmentation:** Isolate critical systems from general network access
2. **Deploy Web Application Firewall (WAF):** Protect against OWASP Top 10 vulnerabilities
3. **Enable Comprehensive Logging:** Implement SIEM for security monitoring and incident response
4. **Conduct Security Code Review:** Review application source code for security flaws
5. **Implement Multi-Factor Authentication (MFA):** Add MFA to all administrative interfaces

### 🟢 Medium Priority (Within 90 Days)
1. **Security Awareness Training:** Educate staff on phishing, social engineering, and security best practices
2. **Vulnerability Management Program:** Establish regular vulnerability scanning and patching procedures
3. **Incident Response Plan:** Develop and test incident response procedures
4. **Data Encryption:** Implement encryption for data at rest and in transit
5. **Regular Penetration Testing:** Schedule quarterly security assessments

---

## 8. Conclusion

"""
    
    if overall_risk in ["CRITICAL", "HIGH"]:
        report += f"""This penetration test revealed significant security concerns with an overall risk rating of **{overall_risk}**. 

**Summary of Critical Issues:**
- {vuln_count} vulnerabilities identified, including {critical_vulns + high_vulns} critical/high severity issues
- {port_count} open ports expanding the attack surface
- {len(missing_headers)} critical security headers missing
- {len([p for p in paths if any(k in p.get('path', '') for k in ['/admin', '/.git'])])} sensitive paths exposed

**Immediate action is required** to address the critical and high-severity findings. The current security posture poses significant risk to the organization's data, systems, and reputation.
"""
    else:
        report += f"""This penetration test identified {vuln_count} security findings with an overall risk rating of **{overall_risk}**. 

While no critical vulnerabilities were discovered, the identified issues should be addressed to maintain a robust security posture. Regular security assessments and continuous monitoring are recommended to ensure ongoing protection against evolving threats.
"""
    
    report += f"""

**Recommendations for Ongoing Security:**
- Implement a continuous vulnerability management program
- Conduct regular penetration tests (minimum quarterly)
- Maintain up-to-date security patches and configurations
- Establish security monitoring and incident response capabilities
- Provide regular security training for all personnel

---

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Assessment Methodology:** OWASP Testing Guide v4 + PTES Standard  
**Tools Used:** Nmap, Nikto, Gobuster, OpenVAS, Custom Scripts  
**Assessment Type:** Black Box Penetration Test  

---

*This report is confidential and intended solely for the use of {org}. Unauthorized distribution is prohibited.*
"""
    
    return report


def get_port_risk_description(port: int) -> str:
    """Return risk description for specific ports."""
    risks = {
        21: "FTP - Cleartext credentials, vulnerable to interception. Use SFTP/FTPS instead",
        23: "Telnet - Unencrypted remote access. Replace with SSH",
        25: "SMTP - Mail server, often targeted for spam relay",
        3306: "MySQL - Database directly exposed to network",
        3389: "RDP - Remote Desktop, frequent brute-force target",
        5900: "VNC - Remote access with weak default security",
        1433: "MS SQL Server - Database access, high-value target",
        5432: "PostgreSQL - Database access requires strong authentication"
    }
    return risks.get(port, "Service exposure increases attack surface")


def get_header_description(header: str) -> str:
    """Return security description for headers."""
    descriptions = {
        "X-Frame-Options": "Prevents clickjacking attacks by controlling iframe embedding",
        "X-XSS-Protection": "Enables browser XSS filtering to prevent cross-site scripting",
        "Content-Security-Policy": "Prevents XSS, clickjacking, and code injection attacks",
        "Strict-Transport-Security": "Forces HTTPS connections to prevent protocol downgrade attacks",
        "X-Content-Type-Options": "Prevents MIME-sniffing attacks",
        "Referrer-Policy": "Controls referrer information leakage"
    }
    return descriptions.get(header, "Security header improves application security posture")


def get_path_risk_description(path: str) -> str:
    """Return risk description for sensitive paths."""
    if '/admin' in path:
        return "Administrative interface exposed - potential unauthorized access"
    elif '/.git' in path:
        return "Git repository exposed - source code and credentials may be accessible"
    elif '/backup' in path:
        return "Backup files exposed - may contain sensitive data or credentials"
    elif '/config' in path:
        return "Configuration files exposed - may reveal sensitive settings"
    elif '/api' in path:
        return "API endpoint exposed - ensure proper authentication and rate limiting"
    else:
        return "Path may expose sensitive information or functionality"
