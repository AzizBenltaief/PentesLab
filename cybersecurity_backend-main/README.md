# PENTESTLAB - Secure Penetration Testing Orchestration Platform

## 🎯 Overview

PENTESTLAB is a comprehensive web-based penetration testing orchestration platform that automates the main phases of security testing including footprinting, scanning, exploitation, post-exploitation, persistence analysis, and reporting. The platform integrates industry-standard open-source security tools (Nmap, OpenVAS, Nikto, Gobuster) in a secure, legal, and traceable manner.

## ✨ Features

### 🔐 Security & Compliance
- **JWT Authentication** - Secure user authentication and authorization
- **Project-based Scope Management** - Define authorized targets for legal compliance
- **Comprehensive Audit Logging** - Track all user actions and scan activities
- **Scope Validation** - Prevent unauthorized scanning outside defined scope

### 🛠️ Integrated Security Tools
- **Nmap** - Network scanning and port discovery
- **OpenVAS** - Comprehensive vulnerability assessment with CVSS scoring
- **Nikto** - Web server vulnerability scanner
- **Gobuster** - Directory and file enumeration
- **Passive Reconnaissance** - WHOIS, DNS, Certificate Transparency, Threat Intelligence

### 📊 Advanced Features
- **9-Phase Pentest Workflow** - Automated orchestration of complete pentesting lifecycle
- **AI-Powered Reporting** - Google Gemini integration for professional report generation
- **CVE/NVD Enrichment** - Vulnerability data enhancement with CVE database
- **Real-time Metrics Dashboard** - Track scan success rates, execution times, and vulnerabilities
- **MongoDB Database** - Flexible NoSQL storage of scans, projects, and audit logs

## 📋 Requirements

### System Requirements
- Docker & Docker Compose (recommended)
- Python 3.11+
- MongoDB 7.0+
- Nmap installed on system

### Technical Skills
- Linux/Unix systems knowledge
- Networking (TCP/IP, DNS, HTTP)
- Security testing fundamentals
- Python and REST APIs

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd cybersecurity_backend-main
```

### 2. Set Up Environment Variables
Create a `.env` file in the root directory:
```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/pentestlab

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production

# AI Integration (Optional)
GEMINI_API_KEY=your-google-gemini-api-key
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
# MongoDB indexes will be created automatically on application startup
# No manual initialization required
```

### 5. Run the Application
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Access API Documentation
Open your browser and navigate to:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🐳 Docker Deployment

### Build and Run with Docker Compose
```bash
docker-compose up --build
```

This will start:
- FastAPI backend on port 8000
- MongoDB database on port 27017
- Mongo Express (web UI) on port 8081 (dev profile)
- Nmap and security tools in isolated container

## 📖 API Usage Guide

### Authentication

#### 1. Register a New User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "pentester",
    "email": "pentester@example.com",
    "password": "SecurePass123!"
  }'
```

#### 2. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "pentester",
    "password": "SecurePass123!"
  }'
```

Save the returned `access_token` for authenticated requests.

### Project Management

#### 3. Create a Project with Scope
```bash
curl -X POST "http://localhost:8000/projects" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Server Pentest",
    "description": "Security assessment of production web servers",
    "scope": ["example.com", "192.168.1.0/24", "testapp.example.com"]
  }'
```

#### 4. List Your Projects
```bash
curl -X GET "http://localhost:8000/projects" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Scanning

#### 5. Start a Pentest Scan
```bash
curl -X POST "http://localhost:8000/scan" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://example.com",
    "project_id": "YOUR_PROJECT_ID"
  }'
```

#### 6. Check Scan Status
```bash
curl -X GET "http://localhost:8000/status/SCAN_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Metrics & Monitoring

#### 7. View Metrics Dashboard
```bash
curl -X GET "http://localhost:8000/metrics/dashboard" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 8. View Audit Logs
```bash
curl -X GET "http://localhost:8000/audit/logs?limit=50" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🔧 Configuration
### Database Configuration
Edit `utils/db.py` or set environment variables:
```python
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "pentestlab"
```ABASE_URL = "postgresql://user:password@host:port/database"
```

### Security Configuration
Edit `auth.py`:
```python
SECRET_KEY = os.getenv("SECRET_KEY", "change-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = 60
```

### AI Report Generation
Set Gemini API key in `.env`:
```env
GEMINI_API_KEY=your-api-key-here
```

## 📊 Pentest Workflow Phases

The platform automates these 9 phases:

1. **Phase 0: Passive Reconnaissance** - WHOIS, DNS, Certificate Transparency, Threat Intel
2. **Phase 1: Footprinting** - HTTP headers, server identification, security headers
3. **Phase 2: Network Scanning** - Nmap port scanning and service detection
4. **Phase 3: Web Vulnerability Scanning** - Nikto and Gobuster
5. **Phase 4: Vulnerability Assessment** - OpenVAS comprehensive scanning with CVE enrichment
6. **Phase 5: Exploitation Analysis** - Vulnerability validation and exploitation checks
7. **Phase 6: Post-Exploitation** - Lateral movement analysis
8. **Phase 7: Persistence Analysis** - Persistence mechanism identification
9. **Phase 8: Reporting** - AI-powered professional report generation

## 📁 Project Structure

```
cybersecurity_backend-main/
├── main.py                 # FastAPI application with all endpoints
├── auth.py                 # JWT authentication and authorization
├── audit.py                # Audit logging system
├── models.py               # Database models (User, Project, ScanResult, AuditLog)
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker containerization
├── docker-compose.yml      # Multi-container orchestration
├── .env.example            # Environment variables template
├── utils/
│   ├── db.py              # Database configuration
│   ├── logger.py          # Logging utilities
│   └── command_runner.py  # Command execution utilities
├── workflow/
│   ├── footprinting.py           # HTTP header analysis
│   ├── scanning.py               # Nmap integration
│   ├── exploitation.py           # Vulnerability checks
│   ├── post_exploitation.py      # Post-exploitation analysis
│   ├── persistence.py            # Persistence checks
│   ├── reporting.py              # AI report generation
│   ├── web_scanning.py           # Nikto & Gobuster integration
│   ├── openvas_integration.py    # OpenVAS & CVE enrichment
│   └── passive_recon.py          # WHOIS, DNS, Shodan-like
└── docs/
    └── API.md              # API documentation
```

## 🔒 Security Best Practices

### For Production Deployment
1. **Change default SECRET_KEY** - Use strong, random secret key
2. **Enable HTTPS** - Use SSL/TLS certificates (Let's Encrypt)
3. **Database Security** - Use strong passwords, enable SSL connections
4. **Rate Limiting** - Implement API rate limiting (use slowapi)
5. **Input Validation** - All inputs are validated via Pydantic
6. **Scope Validation** - Always define project scopes before scanning
7. **Audit Logging** - Review audit logs regularly for compliance

### Legal Compliance
- ⚠️ **IMPORTANT**: Only scan systems you own or have explicit written authorization to test
- Always define project scope before scanning
- Review and comply with local laws and regulations
- Maintain audit logs for accountability
- Use scope validation to prevent unauthorized scanning

## 📈 Metrics & Evaluation

The platform tracks:
- ✅ **Scan Success Rate** - Percentage of successfully completed scans
- ⏱️ **Average Execution Time** - Time per complete pentest campaign
- 🔍 **Vulnerability Coverage** - Total vulnerabilities detected
- 🛡️ **Security Isolation** - Containerized execution environment
- 📊 **User Ergonomics** - Intuitive API and response formats
- ⚖️ **Legal Compliance** - Scope validation and audit trails

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is for educational and authorized security testing purposes only.

## 👥 Authors

- **Houcemeddine HERMASSI** - Project Supervisor

## 🙏 Acknowledgments

- Nmap Project
- OpenVAS/Greenbone
- Nikto
- Gobuster
- FastAPI Framework
- Google Gemini AI

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact project maintainers
- Review documentation at `/docs`

## ⚠️ Disclaimer

This tool is designed for authorized security testing and educational purposes only. Unauthorized access to computer systems is illegal. Users are responsible for complying with all applicable laws and regulations. The authors assume no liability for misuse of this software.

---

**Version**: 2.0.0  
**Last Updated**: January 2026  
**Status**: Production Ready ✅
