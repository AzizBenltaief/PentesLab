# PENTESTLAB - Quick Start Guide

## Starting the Application

### Option 1: Using the Start Script (Recommended)
Simply run the PowerShell script:
```powershell
.\start.ps1
```

This will automatically start both the backend and frontend servers in separate windows.

### Option 2: Manual Start

#### Start Backend:
```powershell
cd cybersecurity_backend-main
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Start Frontend:
```powershell
cd cyber-frontend
npm run dev
```

## Access Points

- **Frontend Application**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MongoDB**: mongodb://localhost:27017

## Default Credentials

Create a new account through the registration page or use your existing credentials.

## Requirements

- MongoDB running on localhost:27017
- Python 3.11+ with dependencies installed
- Node.js 22.22.0+ (currently using nvm)
- Nmap installed (for network scanning)

## Stopping the Application

Close the PowerShell windows or press `Ctrl+C` in each terminal.

## Troubleshooting

### Backend won't start
- Ensure MongoDB is running: `Get-Service MongoDB`
- Check if port 8000 is available

### Frontend won't start
- Ensure Node.js is correctly installed: `node --version`
- Check if port 5173 is available
- Clear node_modules and reinstall: `rm -r node_modules; npm install`

### Nmap not working
- Install Nmap: `choco install nmap -y` (requires admin privileges)
- Or download from: https://nmap.org/download.html

## Project Structure

```
Cyber-Project/
├── cybersecurity_backend-main/    # FastAPI Backend
│   ├── main.py                    # Main application
│   ├── auth.py                    # Authentication
│   ├── models.py                  # Data models
│   ├── workflow/                  # Pentest workflow modules
│   └── utils/                     # Utilities
├── cyber-frontend/                # React Frontend
│   ├── src/
│   │   ├── pages/                 # Page components
│   │   ├── components/            # Reusable components
│   │   └── services/              # API services
│   └── package.json
├── start.ps1                      # Quick start script
└── README.md                      # This file
```

## Features

✅ JWT Authentication
✅ Project-based Scope Management
✅ 9-Phase Pentest Workflow
✅ Real-time Scan Monitoring
✅ AI-Powered Reporting (Gemini)
✅ Comprehensive Audit Logging
✅ MongoDB Database
✅ Modern React UI with Tailwind CSS

## Support

For issues or questions, check the project documentation in `cybersecurity_backend-main/README.md`
