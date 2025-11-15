"""
Pydantic models for predictive analytics and health monitoring.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PredictionType(str, Enum):
    """Types of predictions the system can make."""
    OUTAGE = "OUTAGE"
    BREAKING_CHANGE = "BREAKING_CHANGE"
    PERFORMANCE_DEGRADATION = "PERFORMANCE_DEGRADATION"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    SECURITY_VULNERABILITY = "SECURITY_VULNERABILITY"


class ConfidenceLevel(str, Enum):
    """Confidence levels for predictions."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ImpactLevel(str, Enum):
    """Impact levels for predicted issues."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class HealthStatus(str, Enum):
    """Overall health status of a service."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class PredictiveAlert(BaseModel):
    """
    Predictive alert for potential future issues.

    Attributes:
        alert_id: Unique alert identifier
        prediction_type: Type of prediction
        confidence_score: Confidence score (0-100)
        confidence_level: Confidence level category
        impact_level: Expected impact level
        predicted_occurrence_time: When the issue is predicted to occur
        ai_reasoning: AI explanation of the prediction
        recommended_preventive_actions: Actions to prevent the issue
        affected_services: List of services that may be affected
        created_at: When the prediction was made
    """

    alert_id: str = Field(..., description="Unique alert identifier")
    prediction_type: PredictionType = Field(..., description="Type of prediction")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence score (0-100)")
    confidence_level: ConfidenceLevel = Field(..., description="Confidence level")
    impact_level: ImpactLevel = Field(..., description="Expected impact")
    predicted_occurrence_time: datetime = Field(..., description="Predicted occurrence time")
    ai_reasoning: str = Field(..., description="AI explanation")
    recommended_preventive_actions: List[str] = Field(
        default_factory=list,
        description="Preventive actions"
    )
    affected_services: List[str] = Field(default_factory=list, description="Affected services")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "alert_xyz789",
                "prediction_type": "OUTAGE",
                "confidence_score": 78.5,
                "confidence_level": "HIGH",
                "impact_level": "CRITICAL",
                "predicted_occurrence_time": "2025-01-15T14:00:00Z",
                "ai_reasoning": "Based on increasing error rates and memory usage...",
                "recommended_preventive_actions": [
                    "Scale up service instances",
                    "Clear cache to free memory"
                ],
                "affected_services": ["api-gateway", "auth-service"],
                "created_at": "2025-01-15T10:30:00Z"
            }
        }


class ServiceHealthScore(BaseModel):
    """
    Health score for a service.

    Attributes:
        service_name: Name of the service
        overall_score: Overall health score (0-100)
        health_status: Overall health status
        availability_score: Availability score (0-100)
        performance_score: Performance score (0-100)
        error_rate_score: Error rate score (0-100)
        contributing_factors: Factors affecting the score
        last_updated: When the score was last updated
        trend: Trend direction (improving, stable, degrading)
    """

    service_name: str = Field(..., description="Service name")
    overall_score: float = Field(..., ge=0, le=100, description="Overall health score")
    health_status: HealthStatus = Field(..., description="Health status")
    availability_score: float = Field(..., ge=0, le=100, description="Availability score")
    performance_score: float = Field(..., ge=0, le=100, description="Performance score")
    error_rate_score: float = Field(..., ge=0, le=100, description="Error rate score")
    contributing_factors: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contributing factors"
    )
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    trend: Optional[str] = Field(None, description="Trend direction")

    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "api-gateway",
                "overall_score": 85.5,
                "health_status": "HEALTHY",
                "availability_score": 99.5,
                "performance_score": 82.0,
                "error_rate_score": 75.0,
                "contributing_factors": {
                    "high_error_rate": "Elevated 5xx errors in last hour",
                    "slow_response_time": "P95 latency increased by 20%"
                },
                "last_updated": "2025-01-15T10:30:00Z",
                "trend": "stable"
            }
        }


class OutagePrediction(BaseModel):
    """
    Prediction of potential service outage.

    Attributes:
        service_name: Service that may experience outage
        probability: Probability of outage (0-100)
        predicted_time: When the outage is predicted
        duration_estimate: Estimated duration in minutes
        triggers: Identified triggers
        prevention_steps: Steps to prevent outage
    """

    service_name: str = Field(..., description="Service name")
    probability: float = Field(..., ge=0, le=100, description="Outage probability")
    predicted_time: datetime = Field(..., description="Predicted outage time")
    duration_estimate: Optional[int] = Field(None, description="Estimated duration (minutes)")
    triggers: List[str] = Field(default_factory=list, description="Identified triggers")
    prevention_steps: List[str] = Field(default_factory=list, description="Prevention steps")

    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "database",
                "probability": 85.0,
                "predicted_time": "2025-01-15T14:00:00Z",
                "duration_estimate": 15,
                "triggers": [
                    "Connection pool exhaustion trend",
                    "Memory usage at 95%"
                ],
                "prevention_steps": [
                    "Increase connection pool size",
                    "Restart service to clear memory leaks"
                ]
            }
        }


class PerformanceOptimization(BaseModel):
    """
    Performance optimization recommendation.

    Attributes:
        service_name: Service to optimize
        issue_type: Type of performance issue
        current_metrics: Current performance metrics
        expected_improvement: Expected improvement percentage
        optimization_steps: Steps to optimize
        estimated_effort: Estimated effort level
    """

    service_name: str = Field(..., description="Service name")
    issue_type: str = Field(..., description="Performance issue type")
    current_metrics: Dict[str, Any] = Field(..., description="Current metrics")
    expected_improvement: float = Field(..., description="Expected improvement %")
    optimization_steps: List[str] = Field(default_factory=list, description="Optimization steps")
    estimated_effort: str = Field(..., description="Effort level (low/medium/high)")

    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "api-gateway",
                "issue_type": "High latency",
                "current_metrics": {
                    "p95_latency_ms": 850,
                    "p99_latency_ms": 1200
                },
                "expected_improvement": 40.0,
                "optimization_steps": [
                    "Enable response caching",
                    "Optimize database queries",
                    "Add connection pooling"
                ],
                "estimated_effort": "medium"
            }
        }


class BreakingChangeAlert(BaseModel):
    """
    Alert for potential breaking changes.

    Attributes:
        alert_id: Unique alert identifier
        change_type: Type of breaking change
        affected_components: Components affected
        detected_at: When the change was detected
        impact_analysis: Analysis of the impact
        migration_steps: Steps to migrate
        rollback_plan: Plan to rollback if needed
    """

    alert_id: str = Field(..., description="Alert identifier")
    change_type: str = Field(..., description="Type of breaking change")
    affected_components: List[str] = Field(..., description="Affected components")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Detection time")
    impact_analysis: str = Field(..., description="Impact analysis")
    migration_steps: List[str] = Field(default_factory=list, description="Migration steps")
    rollback_plan: Optional[str] = Field(None, description="Rollback plan")

    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "bc_alert_123",
                "change_type": "API schema change",
                "affected_components": ["mobile-app", "web-frontend"],
                "detected_at": "2025-01-15T10:30:00Z",
                "impact_analysis": "API endpoint /users now requires authentication",
                "migration_steps": [
                    "Update API clients to include auth headers",
                    "Test all affected endpoints"
                ],
                "rollback_plan": "Revert to API v1.2.3 if issues occur"
            }
        }


class DashboardStats(BaseModel):
    """
    Statistics for the dashboard.

    Attributes:
        total_bugs_detected: Total bugs detected
        critical_bugs: Number of critical bugs
        bugs_auto_healed: Number of bugs auto-healed
        active_alerts: Number of active alerts
        services_monitored: Number of services being monitored
        average_health_score: Average health score across services
        recent_predictions: Recent predictive alerts
    """

    total_bugs_detected: int = Field(default=0, description="Total bugs detected")
    critical_bugs: int = Field(default=0, description="Critical bugs")
    bugs_auto_healed: int = Field(default=0, description="Auto-healed bugs")
    active_alerts: int = Field(default=0, description="Active alerts")
    services_monitored: int = Field(default=0, description="Services monitored")
    average_health_score: float = Field(default=0.0, description="Average health score")
    recent_predictions: List[PredictiveAlert] = Field(
        default_factory=list,
        description="Recent predictions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_bugs_detected": 42,
                "critical_bugs": 3,
                "bugs_auto_healed": 28,
                "active_alerts": 5,
                "services_monitored": 8,
                "average_health_score": 87.5,
                "recent_predictions": []
            }
        }
