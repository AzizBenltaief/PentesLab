# FUSE Backend API Documentation

## Overview
The FUSE backend is a FastAPI application that orchestrates a simulated penetration testing workflow. It uses Docker to manage dependencies like Nmap.

## Endpoints

### `POST /scan`
Starts a new pentest scan.

**Request Body:**
```json
{
  "target_url": "https://example.com"
}
```

**Response:**
```json
{
  "scan_id": "uuid-string",
  "message": "Scan started"
}
```

### `GET /status/{scan_id}`
Retrieves the status of a running or completed scan.

**Response:**
```json
{
  "id": "uuid-string",
  "status": "running|completed|failed",
  "step": 0-5,
  "logs": ["log1", "log2"],
  "vulns": 0,
  "results": {
      "headers": {},
      "open_ports": []
  }
}
```

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Workflow Steps
1. **Footprinting**: HTTP Header analysis.
2. **Scanning**: Nmap port scan.
3. **Exploitation**: Vulnerability checks (simulated).
4. **Post-Exploitation**: Analysis of entry points.
5. **Persistence**: Persistence mechanism audit.
6. **Reporting**: Final summary.
