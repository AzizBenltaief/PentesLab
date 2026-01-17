import logging
from datetime import datetime
from typing import Optional, Dict, Any
from utils.db import audit_logs_collection

logger = logging.getLogger(__name__)

class AuditLogger:
    """Centralized audit logging system for legal compliance and traceability (MongoDB)."""
    
    @staticmethod
    async def log_action(
        user_id: Optional[str],
        username: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        status: str = "success"
    ):
        """
        Log an action to the audit trail.
        
        Args:
            user_id: ID of the user performing the action
            username: Username of the user
            action: Action performed (e.g., 'scan_started', 'project_created')
            resource_type: Type of resource (e.g., 'scan', 'project', 'user')
            resource_id: ID of the resource affected
            details: Additional details about the action
            ip_address: IP address of the user
            status: Status of the action ('success', 'failure', 'error')
        """
        try:
            audit_entry = {
                "user_id": user_id,
                "username": username,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
                "ip_address": ip_address,
                "status": status,
                "timestamp": datetime.utcnow()
            }
            await audit_logs_collection.insert_one(audit_entry)
            
            # Also log to file for redundancy
            logger.info(
                f"AUDIT: User={username} ({user_id}) Action={action} "
                f"Resource={resource_type}:{resource_id} Status={status} IP={ip_address}"
            )
        except Exception as e:
            logger.error(f"Failed to write audit log: {str(e)}")
    
    @staticmethod
    async def log_scan_started(user_id: str, username: str, scan_id: str, target: str, ip_address: str):
        """Log when a scan is started."""
        await AuditLogger.log_action(
            user_id=user_id,
            username=username,
            action="scan_started",
            resource_type="scan",
            resource_id=scan_id,
            details={"target": target},
            ip_address=ip_address
        )
    
    @staticmethod
    async def log_scan_completed(user_id: str, username: str, scan_id: str, vulns_found: int):
        """Log when a scan is completed."""
        await AuditLogger.log_action(
            user_id=user_id,
            username=username,
            action="scan_completed",
            resource_type="scan",
            resource_id=scan_id,
            details={"vulnerabilities_found": vulns_found}
        )
    
    @staticmethod
    async def log_project_created(user_id: str, username: str, project_id: str, project_name: str, ip_address: str):
        """Log when a project is created."""
        await AuditLogger.log_action(
            user_id=user_id,
            username=username,
            action="project_created",
            resource_type="project",
            resource_id=project_id,
            details={"project_name": project_name},
            ip_address=ip_address
        )
    
    @staticmethod
    async def log_authentication(username: str, success: bool, ip_address: str, user_id: Optional[str] = None):
        """Log authentication attempts."""
        await AuditLogger.log_action(
            user_id=user_id,
            username=username,
            action="authentication",
            resource_type="user",
            resource_id=user_id,
            details={"success": success},
            ip_address=ip_address,
            status="success" if success else "failure"
        )
    
    @staticmethod
    async def log_scope_validation(user_id: str, username: str, target: str, in_scope: bool, project_id: str):
        """Log scope validation checks."""
        await AuditLogger.log_action(
            user_id=user_id,
            username=username,
            action="scope_validation",
            resource_type="scan",
            resource_id=None,
            details={
                "target": target,
                "in_scope": in_scope,
                "project_id": project_id
            },
            status="success" if in_scope else "failure"
        )
