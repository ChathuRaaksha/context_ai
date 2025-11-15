"""
Monitoring API endpoints for log ingestion, bug detection, and self-healing.
Provides REST API for Grafana integration and dashboard statistics.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query

from app.core.auth import optional_api_key
from app.core.database import get_database
from app.models.bug import (
    AnalysisRequest,
    BugDetection,
    BugList,
    BugSeverity,
    HealingRequest,
    HealingResponse
)
from app.models.predictive import ServiceHealthScore, DashboardStats, HealthStatus
from app.services.bug_detection_service import BugDetectionService
from app.services.self_healing_service import SelfHealingService
from app.services.github_service import GitHubService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["monitoring"])

# Service instances (will be initialized in main.py)
bug_detection_service: Optional[BugDetectionService] = None
self_healing_service: Optional[SelfHealingService] = None
github_service: Optional[GitHubService] = None


def set_services(
    bug_service: BugDetectionService,
    healing_service: SelfHealingService,
    gh_service: GitHubService
):
    """
    Set service instances for the router.

    Args:
        bug_service: Bug detection service instance
        healing_service: Self-healing service instance
        gh_service: GitHub service instance
    """
    global bug_detection_service, self_healing_service, github_service
    bug_detection_service = bug_service
    self_healing_service = healing_service
    github_service = gh_service


@router.post("/logs/ingest", response_model=List[BugDetection])
async def ingest_logs(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    api_key: Optional[str] = Depends(optional_api_key)
):
    """
    Ingest and analyze logs for bug detection.

    Args:
        request: Log analysis request with log entries
        background_tasks: FastAPI background tasks
        api_key: Optional API key for authentication

    Returns:
        List[BugDetection]: Detected bugs

    Raises:
        HTTPException: If analysis fails
    """
    try:
        logger.info(f"Ingesting {len(request.logs)} log entries from {request.service_name}")

        if not bug_detection_service:
            raise HTTPException(status_code=500, detail="Bug detection service not initialized")

        # Analyze logs for bugs
        bugs = await bug_detection_service.analyze_logs(request)

        # Trigger self-healing in background for detected bugs
        if bugs and self_healing_service:
            for bug in bugs:
                # Only auto-heal for non-critical bugs by default
                if bug.severity != BugSeverity.CRITICAL:
                    background_tasks.add_task(trigger_healing_background, bug.bug_id)

        return bugs

    except Exception as e:
        logger.error(f"Log ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Log analysis failed: {str(e)}")


@router.post("/grafana/webhook")
async def grafana_webhook(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    api_key: Optional[str] = Depends(optional_api_key)
):
    """
    Receive alerts from Grafana webhook.

    Args:
        payload: Grafana alert payload
        background_tasks: FastAPI background tasks
        api_key: Optional API key for authentication

    Returns:
        Dict: Acknowledgment response

    Raises:
        HTTPException: If webhook processing fails
    """
    try:
        logger.info(f"Received Grafana webhook: {payload.get('title', 'Unknown')}")

        # Extract alert information
        title = payload.get("title", "Grafana Alert")
        message = payload.get("message", "")
        state = payload.get("state", "alerting")
        rule_url = payload.get("ruleUrl", "")

        # Convert Grafana alert to log entries for analysis
        from app.models.bug import LogEntry

        log_entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            level="ERROR" if state == "alerting" else "WARNING",
            service=payload.get("ruleName", "grafana"),
            message=f"{title}: {message}",
            metadata={
                "source": "grafana",
                "state": state,
                "rule_url": rule_url,
                "raw_payload": payload
            }
        )

        # Analyze the alert
        if bug_detection_service:
            analysis_request = AnalysisRequest(
                logs=[log_entry],
                service_name=payload.get("ruleName", "grafana"),
                time_range="Current"
            )

            bugs = await bug_detection_service.analyze_logs(analysis_request)

            # Trigger healing in background
            if bugs and self_healing_service:
                for bug in bugs:
                    background_tasks.add_task(trigger_healing_background, bug.bug_id)

            return {
                "status": "received",
                "message": f"Analyzed alert and detected {len(bugs)} bugs",
                "bugs_detected": len(bugs)
            }

        return {
            "status": "received",
            "message": "Alert received but analysis service not available"
        }

    except Exception as e:
        logger.error(f"Grafana webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    api_key: Optional[str] = Depends(optional_api_key)
):
    """
    Get dashboard statistics.

    Args:
        api_key: Optional API key for authentication

    Returns:
        DashboardStats: Dashboard statistics

    Raises:
        HTTPException: If stats retrieval fails
    """
    try:
        db = await get_database()

        # Get total bugs
        total_bugs = await db.bugs.count_documents({})

        # Get critical bugs
        critical_bugs = await db.bugs.count_documents({"severity": "CRITICAL"})

        # Get auto-healed bugs
        auto_healed = await db.bugs.count_documents({
            "healing_attempted": True,
            "healing_success": True
        })

        # Get active alerts (bugs from last 24 hours)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        active_alerts = await db.bugs.count_documents({
            "detected_at": {"$gte": last_24h}
        })

        # Get unique services
        services = await db.bugs.distinct("source_service")
        services_monitored = len([s for s in services if s])

        # Calculate average health score (placeholder - would be calculated from actual metrics)
        average_health_score = 85.0  # TODO: Calculate from actual service metrics

        stats = DashboardStats(
            total_bugs_detected=total_bugs,
            critical_bugs=critical_bugs,
            bugs_auto_healed=auto_healed,
            active_alerts=active_alerts,
            services_monitored=services_monitored,
            average_health_score=average_health_score,
            recent_predictions=[]
        )

        return stats

    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/bugs", response_model=BugList)
async def list_bugs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    severity: Optional[BugSeverity] = Query(None, description="Filter by severity"),
    api_key: Optional[str] = Depends(optional_api_key)
):
    """
    List detected bugs with pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Number of bugs per page
        severity: Optional severity filter
        api_key: Optional API key for authentication

    Returns:
        BugList: List of bugs with pagination info

    Raises:
        HTTPException: If listing fails
    """
    try:
        if not bug_detection_service:
            raise HTTPException(status_code=500, detail="Bug detection service not initialized")

        bugs = await bug_detection_service.list_bugs(page, page_size, severity)

        # Get total count
        db = await get_database()
        query = {}
        if severity:
            query["severity"] = severity.value
        total = await db.bugs.count_documents(query)

        return BugList(
            bugs=bugs,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Failed to list bugs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list bugs: {str(e)}")


@router.get("/bugs/{bug_id}", response_model=BugDetection)
async def get_bug(
    bug_id: str,
    api_key: Optional[str] = Depends(optional_api_key)
):
    """
    Get details of a specific bug.

    Args:
        bug_id: Bug identifier
        api_key: Optional API key for authentication

    Returns:
        BugDetection: Bug details

    Raises:
        HTTPException: If bug not found or retrieval fails
    """
    try:
        if not bug_detection_service:
            raise HTTPException(status_code=500, detail="Bug detection service not initialized")

        bug = await bug_detection_service.get_bug(bug_id)

        if not bug:
            raise HTTPException(status_code=404, detail=f"Bug {bug_id} not found")

        return bug

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bug {bug_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bug: {str(e)}")


@router.post("/bugs/{bug_id}/heal", response_model=HealingResponse)
async def trigger_healing(
    bug_id: str,
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="Force healing for high-risk actions"),
    api_key: Optional[str] = Depends(optional_api_key)
):
    """
    Trigger self-healing for a specific bug.

    Args:
        bug_id: Bug identifier
        background_tasks: FastAPI background tasks
        force: Force healing for high-risk actions
        api_key: Optional API key for authentication

    Returns:
        HealingResponse: Healing result

    Raises:
        HTTPException: If healing fails or bug not found
    """
    try:
        if not bug_detection_service or not self_healing_service:
            raise HTTPException(status_code=500, detail="Services not initialized")

        # Get the bug
        bug = await bug_detection_service.get_bug(bug_id)
        if not bug:
            raise HTTPException(status_code=404, detail=f"Bug {bug_id} not found")

        # Attempt healing
        result = await self_healing_service.attempt_healing(bug, force=force)

        # Create GitHub issue if healing failed and GitHub is configured
        if not result["success"] and github_service and github_service.is_configured():
            background_tasks.add_task(create_github_issue_background, bug, result)

        return HealingResponse(
            bug_id=bug_id,
            success=result["success"],
            actions_taken=[a.get("description", a.get("action_type", "Unknown"))
                          for a in result.get("actions_taken", [])],
            message=result["message"],
            requires_approval=result.get("requires_approval", False)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger healing for bug {bug_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Healing failed: {str(e)}")


@router.get("/health/{service_name}", response_model=ServiceHealthScore)
async def get_service_health(
    service_name: str,
    api_key: Optional[str] = Depends(optional_api_key)
):
    """
    Get health score for a specific service.

    Args:
        service_name: Name of the service
        api_key: Optional API key for authentication

    Returns:
        ServiceHealthScore: Service health score

    Raises:
        HTTPException: If health score calculation fails
    """
    try:
        db = await get_database()

        # Get bugs for this service in the last 24 hours
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_bugs = await db.bugs.count_documents({
            "source_service": service_name,
            "detected_at": {"$gte": last_24h}
        })

        # Get critical bugs
        critical_bugs = await db.bugs.count_documents({
            "source_service": service_name,
            "severity": "CRITICAL",
            "detected_at": {"$gte": last_24h}
        })

        # Calculate scores (simplified algorithm)
        # In production, this would use actual metrics from monitoring systems
        error_rate_score = max(0, 100 - (recent_bugs * 5))
        availability_score = max(0, 100 - (critical_bugs * 20))
        performance_score = 85.0  # Placeholder

        overall_score = (error_rate_score + availability_score + performance_score) / 3

        # Determine health status
        if overall_score >= 80:
            health_status = HealthStatus.HEALTHY
        elif overall_score >= 60:
            health_status = HealthStatus.DEGRADED
        else:
            health_status = HealthStatus.CRITICAL

        # Contributing factors
        factors = {}
        if recent_bugs > 5:
            factors["high_error_count"] = f"{recent_bugs} bugs detected in last 24h"
        if critical_bugs > 0:
            factors["critical_bugs"] = f"{critical_bugs} critical bugs detected"

        return ServiceHealthScore(
            service_name=service_name,
            overall_score=round(overall_score, 2),
            health_status=health_status,
            availability_score=round(availability_score, 2),
            performance_score=round(performance_score, 2),
            error_rate_score=round(error_rate_score, 2),
            contributing_factors=factors,
            last_updated=datetime.utcnow(),
            trend="stable"
        )

    except Exception as e:
        logger.error(f"Failed to get health score for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get health score: {str(e)}")


# Background task functions

async def trigger_healing_background(bug_id: str):
    """
    Background task to trigger healing for a bug.

    Args:
        bug_id: Bug identifier
    """
    try:
        if not bug_detection_service or not self_healing_service:
            logger.warning("Services not initialized for background healing")
            return

        bug = await bug_detection_service.get_bug(bug_id)
        if not bug:
            logger.warning(f"Bug {bug_id} not found for background healing")
            return

        result = await self_healing_service.attempt_healing(bug)
        logger.info(f"Background healing for {bug_id}: {result['message']}")

        # Create GitHub issue if healing failed
        if not result["success"] and github_service and github_service.is_configured():
            await create_github_issue_background(bug, result)

    except Exception as e:
        logger.error(f"Background healing failed for {bug_id}: {e}")


async def create_github_issue_background(bug: BugDetection, healing_result: Dict[str, Any]):
    """
    Background task to create GitHub issue.

    Args:
        bug: The detected bug
        healing_result: Healing attempt result
    """
    try:
        if github_service and github_service.is_configured():
            issue = await github_service.create_issue(bug, healing_result)
            if issue:
                logger.info(f"Created GitHub issue for bug {bug.bug_id}: {issue['issue_url']}")
        else:
            logger.debug("GitHub service not configured, skipping issue creation")

    except Exception as e:
        logger.error(f"Failed to create GitHub issue for bug {bug.bug_id}: {e}")
