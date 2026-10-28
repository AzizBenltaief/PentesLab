from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Optional
import socket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import existing workflow functions
from workflow import (
    run_footprinting,
    run_scanning,
    run_exploitation,
    run_post_exploitation,
    run_persistence,
    run_reporting
)

# Import new workflow functions
from workflow.web_scanning import run_nikto, run_gobuster
from workflow.openvas_integration import run_openvas_scan, enrich_with_cve_data
from workflow.passive_recon import whois_lookup, dns_enumeration, shodan_lookup, certificate_transparency_check

# Import authentication and audit
from auth import (
    get_current_user, 
    get_current_active_user, 
    create_access_token, 
    get_password_hash, 
    verify_password,
    Token,
    TokenData
)
from audit import AuditLogger
from models import User, Project, ScanResult, AuditLog, UserFeedback, VulnerabilityCoverage
from utils.db import (
    init_db,
    users_collection,
    projects_collection,
    scan_results_collection,
    audit_logs_collection,
    user_feedback_collection,
    vulnerability_coverage_collection,
    scan_chats_collection
)
from utils.coverage_calculator import calculate_vulnerability_coverage, get_coverage_summary
from agent.copilot import answer_scan_question, analyze_scan
from agent.llm import LLMNotAvailableError, llm_available

app = FastAPI(
    title="PENTESTLAB API",
    description="Secure Penetration Testing Orchestration Platform with MongoDB",
    version="2.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize MongoDB indexes on startup."""
    await init_db()

# In-memory storage for scan results (temporary cache)
scans: Dict[str, Dict] = {}

# ============== PYDANTIC MODELS ==============

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scope: List[str]  # List of authorized targets (IPs, domains)

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scope: Optional[List[str]] = None
    status: Optional[str] = None

class ScanRequest(BaseModel):
    target_url: str
    project_id: Optional[str] = None

class FeedbackCreate(BaseModel):
    rating: int  # 1-5
    category: str  # ergonomie, performance, fonctionnalités, documentation
    comment: Optional[str] = None
    scan_id: Optional[str] = None

class ScanStatus(BaseModel):
    id: str
    status: str
    step: int
    logs: List[str]
    vulns: int
    results: Dict
    execution_time: Optional[int] = None
    success_rate: Optional[int] = None

class ChatRequest(BaseModel):
    question: str
    history: Optional[List[Dict]] = None

# ============== AUTHENTICATION ENDPOINTS ==============

@app.post("/auth/register", response_model=Dict)
async def register(user_data: UserCreate, request: Request):
    """Register a new user."""
    # Check if username exists
    existing_user = await users_collection.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    existing_email = await users_collection.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "is_active": True,
        "is_admin": False,
        "created_at": datetime.utcnow()
    }
    
    result = await users_collection.insert_one(new_user)
    user_id = str(result.inserted_id)
    
    await AuditLogger.log_action(
        user_id=user_id,
        username=new_user["username"],
        action="user_registered",
        resource_type="user",
        resource_id=user_id,
        ip_address=request.client.host
    )
    
    return {
        "message": "User registered successfully",
        "user_id": user_id,
        "username": new_user["username"]
    }

@app.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin, request: Request):
    """Authenticate user and return JWT token."""
    user = await users_collection.find_one({"username": user_data.username})
    
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        await AuditLogger.log_authentication(
            username=user_data.username,
            success=False,
            ip_address=request.client.host
        )
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    
    user_id = str(user["_id"])
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user_id},
        expires_delta=access_token_expires
    )
    
    await AuditLogger.log_authentication(
        username=user["username"],
        success=True,
        ip_address=request.client.host,
        user_id=user_id
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me")
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_active_user)
):
    """Get current authenticated user information."""
    from bson import ObjectId
    user = await users_collection.find_one({"_id": ObjectId(current_user.user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "is_active": user.get("is_active", True),
        "is_admin": user.get("is_admin", False),
        "created_at": user["created_at"]
    }

# ============== PROJECT MANAGEMENT ENDPOINTS ==============

@app.post("/projects", response_model=Dict)
async def create_project(
    project_data: ProjectCreate,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Create a new pentest project with defined scope."""
    project_id = str(uuid.uuid4())
    
    new_project = {
        "id": project_id,
        "name": project_data.name,
        "description": project_data.description,
        "owner_id": current_user.user_id,
        "scope": {"targets": project_data.scope},
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await projects_collection.insert_one(new_project)
    
    await AuditLogger.log_project_created(
        user_id=current_user.user_id,
        username=current_user.username,
        project_id=project_id,
        project_name=project_data.name,
        ip_address=request.client.host
    )
    
    return {
        "project_id": project_id,
        "name": new_project["name"],
        "status": new_project["status"],
        "scope": new_project["scope"],
        "created_at": new_project["created_at"]
    }

@app.get("/projects")
async def list_projects(
    current_user: TokenData = Depends(get_current_active_user)
):
    """List all projects for the current user."""
    projects_cursor = projects_collection.find({"owner_id": current_user.user_id})
    projects_list = await projects_cursor.to_list(length=100)
    
    result_projects = []
    for p in projects_list:
        # Count scans for this project
        scan_count = await scan_results_collection.count_documents({"project_id": p["id"]})
        
        result_projects.append({
            "id": p["id"],
            "name": p["name"],
            "description": p.get("description"),
            "status": p["status"],
            "scope": p["scope"],
            "created_at": p["created_at"],
            "scan_count": scan_count
        })
    
    return {"projects": result_projects}

@app.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Get details of a specific project."""
    project = await projects_collection.find_one({
        "id": project_id,
        "owner_id": current_user.user_id
    })
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get scans for this project
    scans_cursor = scan_results_collection.find({"project_id": project_id})
    scans_list = await scans_cursor.to_list(length=100)
    
    return {
        "id": project["id"],
        "name": project["name"],
        "description": project.get("description"),
        "status": project["status"],
        "scope": project["scope"],
        "created_at": project["created_at"],
        "updated_at": project["updated_at"],
        "scans": [
            {
                "id": s["id"],
                "target": s["target_url"],
                "status": s["status"],
                "vulns": s.get("vulns_count", 0),
                "created_at": s["created_at"]
            }
            for s in scans_list
        ]
    }

@app.put("/projects/{project_id}")
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Update a project."""
    project = await projects_collection.find_one({
        "id": project_id,
        "owner_id": current_user.user_id
    })
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Build update dict
    update_data = {"updated_at": datetime.utcnow()}
    if project_data.name is not None:
        update_data["name"] = project_data.name
    if project_data.description is not None:
        update_data["description"] = project_data.description
    if project_data.scope is not None:
        update_data["scope"] = {"targets": project_data.scope}
    if project_data.status is not None:
        update_data["status"] = project_data.status
    
    await projects_collection.update_one(
        {"id": project_id},
        {"$set": update_data}
    )
    
    await AuditLogger.log_action(
        user_id=current_user.user_id,
        username=current_user.username,
        action="project_updated",
        resource_type="project",
        resource_id=project_id,
        details=update_data,
        ip_address=request.client.host
    )
    
    return {"message": "Project updated successfully", "project_id": project_id}

@app.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Delete a project."""
    project = await projects_collection.find_one({
        "id": project_id,
        "owner_id": current_user.user_id
    })
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await projects_collection.delete_one({"id": project_id})
    
    await AuditLogger.log_action(
        user_id=current_user.user_id,
        username=current_user.username,
        action="project_deleted",
        resource_type="project",
        resource_id=project_id,
        ip_address=request.client.host
    )
    
    return {"message": "Project deleted successfully"}

# ============== SCOPE VALIDATION ==============

async def validate_scope(target: str, project_id: str, user_id: str) -> bool:
    """
    Validate if a target is within the defined project scope.
    This ensures legal compliance by preventing unauthorized scanning.
    """
    project = await projects_collection.find_one({"id": project_id})
    
    if not project:
        print(f"DEBUG: Project not found: {project_id}")
        return False
    
    scope_targets = project.get("scope", {}).get("targets", [])
    print(f"DEBUG: Scope targets: {scope_targets}")
    
    # Normalize target for comparison (remove protocol and trailing slash)
    normalized_target = target.lower()
    for protocol in ['https://', 'http://']:
        if normalized_target.startswith(protocol):
            normalized_target = normalized_target[len(protocol):]
            break
    normalized_target = normalized_target.rstrip('/')
    print(f"DEBUG: Normalized target: {normalized_target}")
    
    # Check if target matches any scope entry
    for scope_target in scope_targets:
        # Normalize scope target too
        normalized_scope = scope_target.lower()
        for protocol in ['https://', 'http://']:
            if normalized_scope.startswith(protocol):
                normalized_scope = normalized_scope[len(protocol):]
                break
        normalized_scope = normalized_scope.rstrip('/')
        print(f"DEBUG: Comparing '{normalized_target}' with '{normalized_scope}'")
        
        # Extract domain from scope (remove path)
        scope_domain = normalized_scope.split('/')[0]
        target_domain = normalized_target.split('/')[0]
        
        # Match if:
        # 1. Exact match of full URLs
        # 2. Same domain (ignoring paths)
        # 3. Target is subdomain of scope
        # 4. Scope is subdomain/path of target
        if normalized_target == normalized_scope or \
           target_domain == scope_domain or \
           normalized_target.startswith(normalized_scope + '/') or \
           normalized_scope.startswith(normalized_target + '/') or \
           normalized_target.endswith('.' + scope_domain) or \
           scope_domain.endswith('.' + target_domain):
            print(f"DEBUG: MATCH FOUND!")
            return True
    
    print(f"DEBUG: No match found")
    return False

# ============== SCANNING ENDPOINTS ==============

async def run_pentest_workflow(scan_id: str, target: str, project_id: Optional[str], user_id: str, username: str):
    """Enhanced pentest workflow with 9 phases including new tools."""
    start_time = datetime.utcnow()
    scans[scan_id]["logs"].append(f"Starting comprehensive pentest of {target}")
    
    def log_callback(msg: str):
        scans[scan_id]["logs"].append(msg)
    
    try:
        # Phase 0: Passive Reconnaissance
        scans[scan_id]["step"] = 0
        scans[scan_id]["logs"].append("Phase 0: Passive Reconnaissance")
        
        await whois_lookup(target, scans[scan_id], log_callback)
        await dns_enumeration(target, scans[scan_id], log_callback)
        
        # Get IP for shodan lookup
        try:
            import socket
            ip_address = socket.gethostbyname(target.replace('https://', '').replace('http://', '').split('/')[0])
            await shodan_lookup(ip_address, scans[scan_id], log_callback)
        except:
            log_callback("Could not resolve IP for threat intelligence lookup")
        
        await certificate_transparency_check(target, scans[scan_id], log_callback)
        
        # Phase 1: Footprinting
        scans[scan_id]["step"] = 1
        scans[scan_id]["logs"].append("Phase 1: Footprinting")
        await run_footprinting(target, scans[scan_id], log_callback)
        
        # Phase 2: Network Scanning
        scans[scan_id]["step"] = 2
        scans[scan_id]["logs"].append("Phase 2: Network Scanning (Nmap)")
        domain = target.replace('https://', '').replace('http://', '').split('/')[0]
        await run_scanning(domain, scans[scan_id], log_callback)
        
        # Phase 3: Web Vulnerability Scanning
        scans[scan_id]["step"] = 3
        scans[scan_id]["logs"].append("Phase 3: Web Vulnerability Scanning")
        
        await run_nikto(target, scans[scan_id], log_callback)
        await run_gobuster(target, scans[scan_id], log_callback)
        
        # Phase 4: Vulnerability Assessment with OpenVAS
        scans[scan_id]["step"] = 4
        scans[scan_id]["logs"].append("Phase 4: OpenVAS Vulnerability Assessment")
        
        await run_openvas_scan(target, scans[scan_id], log_callback)
        
        # Enrich with CVE data
        await enrich_with_cve_data(scans[scan_id], log_callback)
        
        # Phase 5: Exploitation Analysis
        scans[scan_id]["step"] = 5
        scans[scan_id]["logs"].append("Phase 5: Exploitation Analysis")
        await run_exploitation(scans[scan_id], log_callback)
        
        # Phase 6: Post-Exploitation
        scans[scan_id]["step"] = 6
        scans[scan_id]["logs"].append("Phase 6: Post-Exploitation Analysis")
        await run_post_exploitation(scans[scan_id], log_callback)
        
        # Phase 7: Persistence Analysis
        scans[scan_id]["step"] = 7
        scans[scan_id]["logs"].append("Phase 7: Persistence Analysis")
        await run_persistence(scans[scan_id], log_callback)
        
        # Phase 8: AI Report Generation
        scans[scan_id]["step"] = 8
        scans[scan_id]["logs"].append("Phase 8: Generating AI-powered report")
        try:
            report = await run_reporting(scans[scan_id]["results"], target=target)
            scans[scan_id]["results"]["ai_report"] = report
        except Exception as e:
            log_callback(f"AI Report generation skipped: {str(e)}")
            scans[scan_id]["results"]["ai_report"] = "AI Report generation skipped (API key not configured)."
        
        # Calculate metrics - total vulnerabilities already tracked in scan_results["vulns"]
        total_vulns = scans[scan_id]["vulns"]
        scans[scan_id]["vulns"] = total_vulns
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds())
        scans[scan_id]["execution_time"] = execution_time
        scans[scan_id]["success_rate"] = 100  # All phases completed
        
        # Calculate vulnerability coverage
        coverage = calculate_vulnerability_coverage(scans[scan_id]["results"])
        scans[scan_id]["coverage"] = coverage
        
        # Store coverage in database
        coverage_doc = {
            "scan_id": scan_id,
            "total_checks": coverage["total_checks"],
            "passed_checks": coverage["passed_checks"],
            "failed_checks": coverage["failed_checks"],
            "coverage_percentage": coverage["coverage_percentage"],
            "categories": coverage["categories"],
            "timestamp": datetime.utcnow()
        }
        await vulnerability_coverage_collection.insert_one(coverage_doc)
        
        # Save to database
        scan_result = {
            "id": scan_id,
            "user_id": user_id,
            "project_id": project_id,
            "target_url": target,
            "status": "completed",
            "vulns_count": total_vulns,
            "scan_data": scans[scan_id]["results"],
            "ai_report": scans[scan_id]["results"].get("ai_report", "AI Report not generated"),
            "execution_time": execution_time,
            "success_rate": 100,
            "coverage_percentage": coverage["coverage_percentage"],
            "created_at": start_time
        }
        await scan_results_collection.insert_one(scan_result)
        
        scans[scan_id]["status"] = "completed"
        scans[scan_id]["logs"].append(f"Scan completed! Found {total_vulns} vulnerabilities")
        
        await AuditLogger.log_scan_completed(
            user_id=user_id,
            username=username,
            scan_id=scan_id,
            vulns_found=total_vulns
        )
        
    except Exception as e:
        scans[scan_id]["status"] = "failed"
        scans[scan_id]["logs"].append(f"Error: {str(e)}")
        await AuditLogger.log_action(
            user_id=user_id,
            username=username,
            action="scan_failed",
            resource_type="scan",
            resource_id=scan_id,
            details={"error": str(e)},
            status="error"
        )

@app.post("/scan")
async def start_scan(
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Start a new pentest scan with scope validation."""
    target = scan_request.target_url
    project_id = scan_request.project_id
    
    # Validate scope if project_id provided
    if project_id:
        in_scope = await validate_scope(target, project_id, current_user.user_id)
        
        await AuditLogger.log_scope_validation(
            user_id=current_user.user_id,
            username=current_user.username,
            target=target,
            in_scope=in_scope,
            project_id=project_id
        )
        
        if not in_scope:
            raise HTTPException(
                status_code=403,
                detail=f"Target {target} is not in the authorized scope for this project. "
                       "Please add it to the project scope before scanning."
            )
    
    # Generate scan ID
    scan_id = str(uuid.uuid4())
    
    # Initialize scan tracking
    scans[scan_id] = {
        "id": scan_id,
        "status": "running",
        "step": 0,
        "logs": [],
        "vulns": 0,
        "results": {},
        "user_id": current_user.user_id,
        "username": current_user.username,
        "project_id": project_id,
        "target_url": target
    }
    
    # Log scan start
    await AuditLogger.log_scan_started(
        user_id=current_user.user_id,
        username=current_user.username,
        scan_id=scan_id,
        target=target,
        ip_address=request.client.host
    )
    
    # Start background task
    background_tasks.add_task(
        run_pentest_workflow,
        scan_id,
        target,
        project_id,
        current_user.user_id,
        current_user.username
    )
    
    return {
        "scan_id": scan_id, 
        "message": "Scan started with legal compliance validation",
        "project_id": project_id
    }

@app.get("/status/{scan_id}", response_model=ScanStatus)
async def get_status(
    scan_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Get status of a running or completed scan."""
    # First check in-memory for running scans
    if scan_id in scans:
        scan = scans[scan_id]
        if scan["user_id"] != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this scan")
        return scan
    
    # If not in memory, check MongoDB for completed scans
    scan_result = await scan_results_collection.find_one({"id": scan_id})
    if not scan_result:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan_result.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this scan")
    
    # Transform MongoDB document to match expected format
    result_data = {
        "id": scan_result["id"],
        "status": scan_result.get("status", "completed"),
        "step": 8,  # Completed scans are at final step
        "logs": [],  # Logs not stored in MongoDB
        "vulns": scan_result.get("vulns_count", 0),
        "results": scan_result.get("scan_data", {}),
        "execution_time": scan_result.get("execution_time"),
        "success_rate": scan_result.get("success_rate", 100)
    }
    print(f"DEBUG: Returning scan data for {scan_id}")
    print(f"DEBUG: Results keys: {list(result_data['results'].keys()) if result_data['results'] else 'None'}")
    return result_data

@app.get("/metrics/dashboard")
async def get_metrics_dashboard(
    current_user: TokenData = Depends(get_current_active_user)
):
    """Get metrics dashboard for user's scans."""
    # Get running scans from in-memory dictionary
    running_scans_mem = [s for s in scans.values() if s.get("user_id") == current_user.user_id and s["status"] == "running"]
    running_scans_count = len(running_scans_mem)
    
    # Get all scan data from MongoDB
    user_scans_cursor = scan_results_collection.find({"user_id": current_user.user_id})
    user_scans = await user_scans_cursor.to_list(length=None)
    
    # Combine in-memory running scans with MongoDB completed scans
    total_scans = len(user_scans) + running_scans_count
    completed_scans = len([s for s in user_scans if s.get("status") == "completed"])
    failed_scans = len([s for s in user_scans if s.get("status") == "failed"])
    
    # Calculate metrics from MongoDB data
    total_vulns = sum(s.get("vulns_count", 0) for s in user_scans)
    avg_execution_time = sum(s.get("execution_time", 0) for s in user_scans) / len(user_scans) if user_scans else 0
    avg_success_rate = sum(s.get("success_rate", 0) for s in user_scans) / len(user_scans) if user_scans else 0
    
    # Get project count from database
    project_count = await projects_collection.count_documents({"owner_id": current_user.user_id})
    active_project_count = await projects_collection.count_documents({
        "owner_id": current_user.user_id,
        "status": "active"
    })
    
    return {
        "total_scans": total_scans,
        "completed_scans": completed_scans,
        "failed_scans": failed_scans,
        "running_scans": running_scans_count,
        "success_rate": round(avg_success_rate, 2),
        "total_vulnerabilities": total_vulns,
        "avg_execution_time": round(avg_execution_time, 2),
        "total_projects": project_count,
        "active_projects": active_project_count
    }

@app.get("/audit/logs")
async def get_audit_logs(
    limit: int = 100,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Get audit logs for the current user."""
    logs_cursor = audit_logs_collection.find(
        {"user_id": current_user.user_id}
    ).sort("timestamp", -1).limit(limit)
    
    logs_list = await logs_cursor.to_list(length=limit)
    
    return {
        "logs": [
            {
                "id": str(log["_id"]),
                "action": log["action"],
                "resource_type": log["resource_type"],
                "resource_id": log.get("resource_id"),
                "status": log["status"],
                "timestamp": log["timestamp"],
                "details": log.get("details", {})
            }
            for log in logs_list
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": "MongoDB",
        "features": [
            "authentication",
            "project_management",
            "scope_validation",
            "audit_logging",
            "openvas_integration",
            "nikto_scanning",
            "gobuster_enumeration",
            "passive_reconnaissance",
            "cve_enrichment",
            "metrics_dashboard",
            "vulnerability_coverage",
            "user_feedback",
            "advanced_statistics"
        ]
    }

# ============== NEW ENDPOINTS: VULNERABILITY COVERAGE ==============

@app.get("/coverage/{scan_id}")
async def get_vulnerability_coverage(
    scan_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Get vulnerability coverage analysis for a scan."""
    # Get scan results
    scan_result = await scan_results_collection.find_one({"id": scan_id})
    if not scan_result:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan_result.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Calculate coverage
    coverage = calculate_vulnerability_coverage(scan_result.get("scan_data", {}))
    coverage["scan_id"] = scan_id
    coverage["summary"] = get_coverage_summary(coverage)
    
    # Store coverage in database
    coverage_doc = {
        "scan_id": scan_id,
        "total_checks": coverage["total_checks"],
        "passed_checks": coverage["passed_checks"],
        "failed_checks": coverage["failed_checks"],
        "coverage_percentage": coverage["coverage_percentage"],
        "categories": coverage["categories"],
        "timestamp": datetime.utcnow()
    }
    
    # Update or insert coverage
    await vulnerability_coverage_collection.update_one(
        {"scan_id": scan_id},
        {"$set": coverage_doc},
        upsert=True
    )
    
    return coverage

@app.get("/coverage/stats/global")
async def get_global_coverage_stats(
    current_user: TokenData = Depends(get_current_active_user)
):
    """Get global coverage statistics for all user scans."""
    # Get all user scans
    user_scans_cursor = scan_results_collection.find({"user_id": current_user.user_id})
    user_scans = await user_scans_cursor.to_list(length=None)
    
    if not user_scans:
        return {
            "total_scans": 0,
            "avg_coverage": 0,
            "best_coverage": 0,
            "worst_coverage": 0,
            "category_averages": {}
        }
    
    all_coverages = []
    category_totals = {}
    
    for scan in user_scans:
        coverage = calculate_vulnerability_coverage(scan.get("scan_data", {}))
        all_coverages.append(coverage["coverage_percentage"])
        
        for cat_name, cat_data in coverage["categories"].items():
            if cat_name not in category_totals:
                category_totals[cat_name] = []
            category_totals[cat_name].append(cat_data["percentage"])
    
    # Calculate statistics
    avg_coverage = sum(all_coverages) / len(all_coverages) if all_coverages else 0
    best_coverage = max(all_coverages) if all_coverages else 0
    worst_coverage = min(all_coverages) if all_coverages else 0
    
    category_averages = {
        cat: round(sum(percentages) / len(percentages), 2)
        for cat, percentages in category_totals.items()
    }
    
    return {
        "total_scans": len(user_scans),
        "avg_coverage": round(avg_coverage, 2),
        "best_coverage": round(best_coverage, 2),
        "worst_coverage": round(worst_coverage, 2),
        "category_averages": category_averages
    }

# ============== NEW ENDPOINTS: ADVANCED STATISTICS ==============

@app.get("/statistics/execution-times")
async def get_execution_time_statistics(
    current_user: TokenData = Depends(get_current_active_user)
):
    """Get detailed execution time statistics."""
    user_scans_cursor = scan_results_collection.find({"user_id": current_user.user_id})
    user_scans = await user_scans_cursor.to_list(length=None)
    
    if not user_scans:
        return {
            "total_scans": 0,
            "avg_time": 0,
            "min_time": 0,
            "max_time": 0,
            "median_time": 0,
            "std_deviation": 0,
            "time_distribution": []
        }
    
    execution_times = [s.get("execution_time", 0) for s in user_scans if s.get("execution_time")]
    
    if not execution_times:
        return {"total_scans": len(user_scans), "avg_time": 0}
    
    # Calculate statistics
    avg_time = sum(execution_times) / len(execution_times)
    min_time = min(execution_times)
    max_time = max(execution_times)
    
    # Calculate median
    sorted_times = sorted(execution_times)
    n = len(sorted_times)
    median_time = sorted_times[n // 2] if n % 2 == 1 else (sorted_times[n // 2 - 1] + sorted_times[n // 2]) / 2
    
    # Calculate standard deviation
    variance = sum((x - avg_time) ** 2 for x in execution_times) / len(execution_times)
    std_deviation = variance ** 0.5
    
    # Time distribution (bins)
    time_bins = {
        "0-30s": sum(1 for t in execution_times if t < 30),
        "30-60s": sum(1 for t in execution_times if 30 <= t < 60),
        "60-120s": sum(1 for t in execution_times if 60 <= t < 120),
        "120s+": sum(1 for t in execution_times if t >= 120)
    }
    
    return {
        "total_scans": len(user_scans),
        "avg_time": round(avg_time, 2),
        "min_time": round(min_time, 2),
        "max_time": round(max_time, 2),
        "median_time": round(median_time, 2),
        "std_deviation": round(std_deviation, 2),
        "time_distribution": time_bins,
        "recent_scans": [
            {
                "id": s["id"],
                "target": s.get("target_url"),
                "execution_time": s.get("execution_time", 0),
                "created_at": s.get("created_at")
            }
            for s in sorted(user_scans, key=lambda x: x.get("created_at", datetime.min), reverse=True)[:10]
        ]
    }

# ============== NEW ENDPOINTS: USER FEEDBACK ==============

@app.post("/feedback")
async def submit_feedback(
    feedback: FeedbackCreate,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Submit user feedback for ergonomics evaluation."""
    # Validate rating
    if not 1 <= feedback.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Validate category
    valid_categories = ["ergonomie", "performance", "fonctionnalités", "documentation"]
    if feedback.category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Category must be one of: {', '.join(valid_categories)}"
        )
    
    # Create feedback document
    feedback_doc = {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "rating": feedback.rating,
        "category": feedback.category,
        "comment": feedback.comment,
        "scan_id": feedback.scan_id,
        "timestamp": datetime.utcnow()
    }
    
    # Insert into database
    result = await user_feedback_collection.insert_one(feedback_doc)
    
    # Log audit
    await AuditLogger.log_action(
        user_id=current_user.user_id,
        username=current_user.username,
        action="submit_feedback",
        resource_type="feedback",
        resource_id=str(result.inserted_id),
        details={"rating": feedback.rating, "category": feedback.category},
        ip_address=request.client.host,
        status="success"
    )
    
    return {
        "message": "Feedback submitted successfully",
        "feedback_id": str(result.inserted_id)
    }

@app.get("/feedback/statistics")
async def get_feedback_statistics(
    current_user: TokenData = Depends(get_current_active_user)
):
    """Get aggregated feedback statistics (admin or personal)."""
    # Get all feedback (for now, user can see all to evaluate platform)
    all_feedback_cursor = user_feedback_collection.find({})
    all_feedback = await all_feedback_cursor.to_list(length=None)
    
    if not all_feedback:
        return {
            "total_feedback": 0,
            "overall_rating": 0,
            "category_ratings": {},
            "recent_comments": []
        }
    
    # Calculate overall rating
    overall_rating = sum(f["rating"] for f in all_feedback) / len(all_feedback)
    
    # Calculate category ratings
    category_ratings = {}
    for category in ["ergonomie", "performance", "fonctionnalités", "documentation"]:
        cat_feedback = [f for f in all_feedback if f["category"] == category]
        if cat_feedback:
            category_ratings[category] = {
                "avg_rating": round(sum(f["rating"] for f in cat_feedback) / len(cat_feedback), 2),
                "total_responses": len(cat_feedback),
                "distribution": {
                    "5_stars": sum(1 for f in cat_feedback if f["rating"] == 5),
                    "4_stars": sum(1 for f in cat_feedback if f["rating"] == 4),
                    "3_stars": sum(1 for f in cat_feedback if f["rating"] == 3),
                    "2_stars": sum(1 for f in cat_feedback if f["rating"] == 2),
                    "1_star": sum(1 for f in cat_feedback if f["rating"] == 1)
                }
            }
    
    # Recent comments
    recent_comments = [
        {
            "category": f["category"],
            "rating": f["rating"],
            "comment": f.get("comment", ""),
            "timestamp": f["timestamp"]
        }
        for f in sorted(all_feedback, key=lambda x: x["timestamp"], reverse=True)[:10]
        if f.get("comment")
    ]
    
    return {
        "total_feedback": len(all_feedback),
        "overall_rating": round(overall_rating, 2),
        "category_ratings": category_ratings,
        "recent_comments": recent_comments
    }

@app.get("/feedback/my-feedback")
async def get_my_feedback(
    current_user: TokenData = Depends(get_current_active_user)
):
    """Get current user's feedback history."""
    my_feedback_cursor = user_feedback_collection.find(
        {"user_id": current_user.user_id}
    ).sort("timestamp", -1)
    
    my_feedback = await my_feedback_cursor.to_list(length=None)
    
    return {
        "total_feedback": len(my_feedback),
        "feedback": [
            {
                "id": str(f["_id"]),
                "category": f["category"],
                "rating": f["rating"],
                "comment": f.get("comment"),
                "scan_id": f.get("scan_id"),
                "timestamp": f["timestamp"]
            }
            for f in my_feedback
        ]
    }

# ============== NEW ENDPOINTS: AI SECURITY COPILOT ==============

async def _resolve_scan_for_user(scan_id: str, user_id: str) -> Optional[Dict]:
    """Locate a scan (in-memory running or completed in MongoDB) and verify ownership.

    Returns a dict with target, results, vulns, status - or None if not found.
    Raises 403 HTTPException if the scan belongs to another user.
    """
    # Running scans live in memory
    if scan_id in scans:
        scan = scans[scan_id]
        if scan.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this scan")
        return {
            "target": scan.get("target_url", ""),
            "results": scan.get("results", {}),
            "vulns": scan.get("vulns", 0),
            "status": scan.get("status", "running")
        }

    # Completed scans live in MongoDB
    scan_result = await scan_results_collection.find_one({"id": scan_id})
    if not scan_result:
        return None

    if scan_result.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this scan")

    return {
        "target": scan_result.get("target_url", ""),
        "results": scan_result.get("scan_data", {}),
        "vulns": scan_result.get("vulns_count", 0),
        "status": scan_result.get("status", "completed")
    }


@app.get("/scan/{scan_id}/chat/history")
async def get_chat_history(
    scan_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Get persisted copilot conversation for a scan."""
    scan = await _resolve_scan_for_user(scan_id, current_user.user_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    chat_doc = await scan_chats_collection.find_one({
        "scan_id": scan_id,
        "user_id": current_user.user_id
    })

    return {
        "scan_id": scan_id,
        "messages": (chat_doc or {}).get("messages", [])
    }


@app.post("/scan/{scan_id}/chat")
async def chat_with_copilot(
    scan_id: str,
    chat_request: ChatRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Ask the AI copilot a question about a specific scan's results."""
    question = chat_request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if len(question) > 2000:
        raise HTTPException(status_code=400, detail="Question too long (max 2000 characters)")

    # Cap client-provided history to the last 12 messages
    history = (chat_request.history or [])[-12:]

    scan = await _resolve_scan_for_user(scan_id, current_user.user_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if not scan["results"]:
        # No results at all yet
        raise HTTPException(
            status_code=409,
            detail="Scan has no results yet. Ask again once the first phases have completed."
        )

    if not llm_available():
        raise HTTPException(
            status_code=503,
            detail="AI Copilot is not available (GROQ_API_KEY not configured on the server)."
        )

    try:
        answer = await answer_scan_question(
            question=question,
            scan_results=scan["results"],
            target=scan["target"],
            history=history
        )
    except LLMNotAvailableError as e:
        raise HTTPException(status_code=502, detail=f"AI Copilot error: {str(e)}")

    # Persist conversation
    now = datetime.utcnow()
    new_messages = [
        {"role": "user", "content": question, "timestamp": now},
        {"role": "assistant", "content": answer, "timestamp": now}
    ]
    await scan_chats_collection.update_one(
        {"scan_id": scan_id, "user_id": current_user.user_id},
        {
            "$push": {"messages": {"$each": new_messages}},
            "$set": {"updated_at": now},
            "$setOnInsert": {"created_at": now}
        },
        upsert=True
    )

    await AuditLogger.log_action(
        user_id=current_user.user_id,
        username=current_user.username,
        action="copilot_chat",
        resource_type="scan",
        resource_id=scan_id,
        details={"question_length": len(question)},
        ip_address=request.client.host
    )

    return {
        "scan_id": scan_id,
        "answer": answer,
        "messages": new_messages
    }


@app.get("/scan/{scan_id}/analysis")
async def get_ai_analysis(
    scan_id: str,
    request: Request,
    force: bool = False,
    current_user: TokenData = Depends(get_current_active_user)
):
    """Get (or generate) the AI triage analysis for a scan.

    Results are cached on the scan document; use ?force=true to regenerate.
    """
    scan = await _resolve_scan_for_user(scan_id, current_user.user_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if not llm_available():
        raise HTTPException(
            status_code=503,
            detail="AI Copilot is not available (GROQ_API_KEY not configured on the server)."
        )

    # Serve cached analysis from MongoDB when available
    if not force:
        scan_result = await scan_results_collection.find_one(
            {"id": scan_id},
            {"ai_analysis": 1}
        )
        cached = (scan_result or {}).get("ai_analysis")
        if cached and cached.get("content"):
            return {
                "scan_id": scan_id,
                "analysis": cached["content"],
                "generated_at": cached.get("generated_at"),
                "cached": True
            }

    try:
        analysis = await analyze_scan(
            scan_results=scan["results"],
            target=scan["target"]
        )
    except LLMNotAvailableError as e:
        raise HTTPException(status_code=502, detail=f"AI Copilot error: {str(e)}")

    generated_at = datetime.utcnow()

    # Cache on the MongoDB scan document (skip for scans not yet persisted)
    await scan_results_collection.update_one(
        {"id": scan_id},
        {"$set": {
            "ai_analysis": {
                "content": analysis,
                "generated_at": generated_at
            }
        }}
    )

    await AuditLogger.log_action(
        user_id=current_user.user_id,
        username=current_user.username,
        action="copilot_analysis",
        resource_type="scan",
        resource_id=scan_id,
        details={"force": force},
        ip_address=request.client.host
    )

    return {
        "scan_id": scan_id,
        "analysis": analysis,
        "generated_at": generated_at,
        "cached": False
    }
