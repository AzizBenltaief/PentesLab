# PENTESTLAB Frontend

A modern React-based web application for orchestrating and managing penetration testing workflows.

## Features

### 🔐 Authentication & Authorization
- User registration and login with JWT authentication
- Protected routes with role-based access control
- Secure session management

### 📁 Project Management
- Create and manage penetration testing projects
- Define authorized target scopes (IP addresses, domains, URLs)
- Track project status and scan history
- Update and delete projects

### 🎯 Comprehensive Scanning Workflow
The platform implements a complete 9-phase penetration testing workflow:

1. **Passive Reconnaissance** - WHOIS lookup, DNS enumeration, Threat intelligence, Certificate transparency checks
2. **Footprinting** - HTTP header analysis, Technology detection
3. **Network Scanning** - Nmap port scanning, Service detection
4. **Web Vulnerability Scanning** - Nikto web server scanning, Gobuster directory enumeration
5. **OpenVAS Vulnerability Assessment** - Comprehensive vulnerability scanning, CVE data enrichment
6. **Exploitation Analysis** - Vulnerability prioritization, Exploit recommendations
7. **Post-Exploitation Analysis** - Entry point analysis, Lateral movement opportunities
8. **Persistence Analysis** - Persistence mechanism identification
9. **AI-Powered Report Generation** - Automated security report creation

### 📊 Dashboard & Metrics
- Real-time metrics and statistics
- Scan status distribution visualization
- Project overview with vulnerability counts
- Success rate and execution time tracking

### 📝 Audit Logging
- Complete activity tracking
- User action monitoring
- Search and filter capabilities

### 🛡️ Legal Compliance
- Scope validation before scanning
- Authorized target verification
- Comprehensive audit trail

## Tech Stack

- React 18, Vite, React Router v6, Axios, Tailwind CSS, Recharts, Lucide React

## Getting Started

### Installation

```bash
npm install
npm run dev
```

The application will be available at http://localhost:5173

Backend API should be running on http://localhost:8000

## License

Educational cybersecurity platform for legal and ethical penetration testing training.
