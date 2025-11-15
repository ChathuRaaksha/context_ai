"""
Pydantic models for bug detection and analysis.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BugSeverity(str, Enum):
    """Severity levels for detected bugs."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class BugCategory(str, Enum):
    """Categories of bugs that can be detected."""
    DATABASE = "DATABASE"
    MEMORY = "MEMORY"
    NETWORK = "NETWORK"
    DISK = "DISK"
    APPLICATION = "APPLICATION"
    SECURITY = "SECURITY"


class LogEntry(BaseModel):
    """
    Individual log entry for analysis.

    Attributes:
        timestamp: When the log was created
        level: Log level (INFO, WARNING, ERROR, etc.)
        service: Service that generated the log
        message: Log message content
        metadata: Additional metadata
    """

    timestamp: str = Field(..., description="ISO format timestamp")
    level: str = Field(..., description="Log level")
    service: str = Field(..., description="Source service name")
    message: str = Field(..., description="Log message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-01-15T10:30:00Z",
                "level": "ERROR",
                "service": "api-gateway",
                "message": "Database connection failed",
                "metadata": {"error_code": "DB_CONN_001"}
            }
        }


class AnalysisRequest(BaseModel):
    """
    Request model for log analysis.

    Attributes:
        logs: List of log entries to analyze
        service_name: Optional service name for context
        time_range: Optional time range description
    """

    logs: List[LogEntry] = Field(..., min_length=1, description="Log entries to analyze")
    service_name: Optional[str] = Field(None, description="Service name for context")
    time_range: Optional[str] = Field(None, description="Time range of logs")

    class Config:
        json_schema_extra = {
            "example": {
                "logs": [
                    {
                        "timestamp": "2025-01-15T10:30:00Z",
                        "level": "ERROR",
                        "service": "api-gateway",
                        "message": "Database connection failed"
                    }
                ],
                "service_name": "api-gateway",
                "time_range": "Last 5 minutes"
            }
        }


class BugDetection(BaseModel):
    """
    Detected bug with AI analysis.

    Attributes:
        bug_id: Unique identifier for the bug
        title: Brief title of the bug
        description: Detailed description
        severity: Bug severity level
        category: Bug category
        ai_analysis: AI-generated analysis
        root_cause: Identified root cause
        recommended_actions: List of recommended fixes
        confidence_score: AI confidence score (0-100)
        healing_attempted: Whether healing was attempted
        healing_success: Whether healing was successful
        detected_at: Timestamp when bug was detected
        source_service: Service where bug was detected
    """

    bug_id: str = Field(..., description="Unique bug identifier")
    title: str = Field(..., description="Bug title")
    description: str = Field(..., description="Detailed description")
    severity: BugSeverity = Field(..., description="Severity level")
    category: BugCategory = Field(..., description="Bug category")
    ai_analysis: str = Field(..., description="AI-generated analysis")
    root_cause: Optional[str] = Field(None, description="Root cause analysis")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence score (0-100)")
    healing_attempted: bool = Field(default=False, description="Whether healing was attempted")
    healing_success: Optional[bool] = Field(None, description="Whether healing succeeded")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")
    source_service: Optional[str] = Field(None, description="Source service")

    class Config:
        json_schema_extra = {
            "example": {
                "bug_id": "bug_abc123",
                "title": "Database Connection Pool Exhausted",
                "description": "All database connections in the pool are in use",
                "severity": "HIGH",
                "category": "DATABASE",
                "ai_analysis": "The connection pool has reached its maximum size...",
                "root_cause": "Connection leak in user authentication service",
                "recommended_actions": [
                    "Increase connection pool size",
                    "Fix connection leak in auth service"
                ],
                "confidence_score": 85.5,
                "healing_attempted": True,
                "healing_success": True,
                "detected_at": "2025-01-15T10:30:00Z",
                "source_service": "api-gateway"
            }
        }


class BugList(BaseModel):
    """
    List of bugs with pagination info.

    Attributes:
        bugs: List of detected bugs
        total: Total number of bugs
        page: Current page number
        page_size: Number of bugs per page
    """

    bugs: List[BugDetection] = Field(..., description="List of bugs")
    total: int = Field(..., description="Total number of bugs")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=50, description="Items per page")


class HealingRequest(BaseModel):
    """
    Request to trigger healing for a bug.

    Attributes:
        bug_id: ID of the bug to heal
        force: Whether to force healing even for high-risk actions
        approval: Approval from user for high-risk actions
    """

    bug_id: str = Field(..., description="Bug ID to heal")
    force: bool = Field(default=False, description="Force healing for high-risk actions")
    approval: Optional[str] = Field(None, description="Approval token for high-risk actions")


class HealingResponse(BaseModel):
    """
    Response from healing attempt.

    Attributes:
        bug_id: ID of the bug
        success: Whether healing was successful
        actions_taken: List of actions that were taken
        message: Status message
        requires_approval: Whether manual approval is required
    """

    bug_id: str = Field(..., description="Bug ID")
    success: bool = Field(..., description="Whether healing succeeded")
    actions_taken: List[str] = Field(default_factory=list, description="Actions taken")
    message: str = Field(..., description="Status message")
    requires_approval: bool = Field(default=False, description="Whether approval is required")

    class Config:
        json_schema_extra = {
            "example": {
                "bug_id": "bug_abc123",
                "success": True,
                "actions_taken": ["Restarted service", "Cleared connection pool"],
                "message": "Healing completed successfully",
                "requires_approval": False
            }
        }
