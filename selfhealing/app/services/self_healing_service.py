"""
Self-healing service for automated bug remediation.
Provides intelligent healing actions based on bug category and risk level.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from app.core.config import settings
from app.core.database import get_database
from app.models.bug import BugDetection, BugCategory

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk levels for healing actions."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class HealingAction:
    """
    Represents a healing action that can be taken.

    Attributes:
        action_type: Type of action (restart, clear_cache, etc.)
        description: Human-readable description
        risk_level: Risk level of the action
        requires_approval: Whether manual approval is needed
        command: Optional command to execute
    """

    def __init__(
        self,
        action_type: str,
        description: str,
        risk_level: RiskLevel,
        requires_approval: bool = False,
        command: Optional[str] = None
    ):
        self.action_type = action_type
        self.description = description
        self.risk_level = risk_level
        self.requires_approval = requires_approval
        self.command = command


class SelfHealingService:
    """
    Service for automated self-healing of detected bugs.

    Implements risk-based automation where low and medium risk actions
    can be auto-approved based on configuration.
    """

    def __init__(self):
        """Initialize the self-healing service."""
        self.db = None
        self._healing_actions = self._initialize_healing_actions()

    async def initialize(self):
        """Initialize database connection."""
        self.db = await get_database()

    def _initialize_healing_actions(self) -> Dict[BugCategory, List[HealingAction]]:
        """
        Initialize predefined healing actions for each bug category.

        Returns:
            Dict[BugCategory, List[HealingAction]]: Healing actions by category
        """
        return {
            BugCategory.DATABASE: [
                HealingAction(
                    action_type="restart_connection_pool",
                    description="Restart database connection pool",
                    risk_level=RiskLevel.LOW
                ),
                HealingAction(
                    action_type="clear_connections",
                    description="Clear stale database connections",
                    risk_level=RiskLevel.LOW
                ),
                HealingAction(
                    action_type="increase_pool_size",
                    description="Increase connection pool size",
                    risk_level=RiskLevel.MEDIUM
                ),
                HealingAction(
                    action_type="restart_service",
                    description="Restart database service",
                    risk_level=RiskLevel.HIGH,
                    requires_approval=True
                ),
            ],
            BugCategory.MEMORY: [
                HealingAction(
                    action_type="clear_cache",
                    description="Clear application cache to free memory",
                    risk_level=RiskLevel.LOW
                ),
                HealingAction(
                    action_type="garbage_collection",
                    description="Force garbage collection",
                    risk_level=RiskLevel.LOW
                ),
                HealingAction(
                    action_type="restart_service",
                    description="Restart service to clear memory leaks",
                    risk_level=RiskLevel.MEDIUM
                ),
                HealingAction(
                    action_type="increase_memory_limit",
                    description="Increase memory allocation limit",
                    risk_level=RiskLevel.HIGH,
                    requires_approval=True
                ),
            ],
            BugCategory.NETWORK: [
                HealingAction(
                    action_type="retry_connection",
                    description="Retry network connection",
                    risk_level=RiskLevel.LOW
                ),
                HealingAction(
                    action_type="reset_connection_pool",
                    description="Reset network connection pool",
                    risk_level=RiskLevel.LOW
                ),
                HealingAction(
                    action_type="switch_endpoint",
                    description="Switch to backup endpoint",
                    risk_level=RiskLevel.MEDIUM
                ),
                HealingAction(
                    action_type="restart_network_service",
                    description="Restart network service",
                    risk_level=RiskLevel.HIGH,
                    requires_approval=True
                ),
            ],
            BugCategory.DISK: [
                HealingAction(
                    action_type="clear_temp_files",
                    description="Clear temporary files",
                    risk_level=RiskLevel.LOW
                ),
                HealingAction(
                    action_type="clear_logs",
                    description="Clear old log files",
                    risk_level=RiskLevel.LOW
                ),
                HealingAction(
                    action_type="compress_files",
                    description="Compress large files",
                    risk_level=RiskLevel.MEDIUM
                ),
                HealingAction(
                    action_type="increase_disk_quota",
                    description="Increase disk quota",
                    risk_level=RiskLevel.HIGH,
                    requires_approval=True
                ),
            ],
            BugCategory.APPLICATION: [
                HealingAction(
                    action_type="clear_cache",
                    description="Clear application cache",
                    risk_level=RiskLevel.LOW
                ),
                HealingAction(
                    action_type="reload_configuration",
                    description="Reload application configuration",
                    risk_level=RiskLevel.MEDIUM
                ),
                HealingAction(
                    action_type="restart_service",
                    description="Restart application service",
                    risk_level=RiskLevel.MEDIUM
                ),
                HealingAction(
                    action_type="rollback_deployment",
                    description="Rollback to previous deployment",
                    risk_level=RiskLevel.HIGH,
                    requires_approval=True
                ),
            ],
            BugCategory.SECURITY: [
                HealingAction(
                    action_type="revoke_tokens",
                    description="Revoke suspicious authentication tokens",
                    risk_level=RiskLevel.MEDIUM
                ),
                HealingAction(
                    action_type="enable_rate_limiting",
                    description="Enable rate limiting",
                    risk_level=RiskLevel.LOW
                ),
                HealingAction(
                    action_type="block_ip",
                    description="Block suspicious IP addresses",
                    risk_level=RiskLevel.HIGH,
                    requires_approval=True
                ),
                HealingAction(
                    action_type="rotate_credentials",
                    description="Rotate security credentials",
                    risk_level=RiskLevel.HIGH,
                    requires_approval=True
                ),
            ],
        }

    async def attempt_healing(
        self,
        bug: BugDetection,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Attempt to heal a detected bug.

        Args:
            bug: The bug to heal
            force: Whether to force healing even for high-risk actions

        Returns:
            Dict[str, Any]: Healing result with success status and actions taken
        """
        logger.info(f"Attempting to heal bug {bug.bug_id} ({bug.category})")

        # Get available healing actions for this bug category
        actions = self._healing_actions.get(bug.category, [])

        if not actions:
            logger.warning(f"No healing actions available for category {bug.category}")
            return {
                "success": False,
                "message": f"No healing actions available for {bug.category}",
                "actions_taken": [],
                "requires_approval": False
            }

        # Filter actions based on risk and configuration
        applicable_actions = self._filter_applicable_actions(actions, force)

        if not applicable_actions:
            logger.info(f"All actions for bug {bug.bug_id} require manual approval")
            return {
                "success": False,
                "message": "All available actions require manual approval",
                "actions_taken": [],
                "requires_approval": True,
                "available_actions": [
                    {
                        "action_type": action.action_type,
                        "description": action.description,
                        "risk_level": action.risk_level.value
                    }
                    for action in actions
                ]
            }

        # Execute healing actions
        actions_taken = []
        success = False

        for action in applicable_actions:
            try:
                result = await self._execute_action(action, bug)
                actions_taken.append({
                    "action_type": action.action_type,
                    "description": action.description,
                    "status": "success" if result else "failed"
                })

                if result:
                    success = True
                    # For now, we stop after first successful action
                    break

            except Exception as e:
                logger.error(f"Failed to execute action {action.action_type}: {e}")
                actions_taken.append({
                    "action_type": action.action_type,
                    "description": action.description,
                    "status": "error",
                    "error": str(e)
                })

        # Update bug status
        await self._update_bug_status(bug.bug_id, success, actions_taken)

        # Log healing attempt
        await self._log_healing_attempt(bug.bug_id, actions_taken, success)

        return {
            "success": success,
            "message": "Healing completed" if success else "Healing failed",
            "actions_taken": actions_taken,
            "requires_approval": False
        }

    def _filter_applicable_actions(
        self,
        actions: List[HealingAction],
        force: bool
    ) -> List[HealingAction]:
        """
        Filter actions based on risk level and configuration.

        Args:
            actions: List of available actions
            force: Whether to force high-risk actions

        Returns:
            List[HealingAction]: Applicable actions
        """
        applicable = []

        for action in actions:
            # Check if action is auto-approved based on risk level
            if action.risk_level == RiskLevel.LOW and settings.AUTO_HEAL_LOW_RISK:
                applicable.append(action)
            elif action.risk_level == RiskLevel.MEDIUM and settings.AUTO_HEAL_MEDIUM_RISK:
                applicable.append(action)
            elif action.risk_level == RiskLevel.HIGH and (settings.AUTO_HEAL_HIGH_RISK or force):
                applicable.append(action)

        return applicable

    async def _execute_action(
        self,
        action: HealingAction,
        bug: BugDetection
    ) -> bool:
        """
        Execute a healing action.

        Args:
            action: The action to execute
            bug: The bug being healed

        Returns:
            bool: True if action was successful

        Note:
            This is a simulation. In production, this would execute actual
            remediation commands (restart services, clear caches, etc.)
        """
        logger.info(f"Executing healing action: {action.action_type} for bug {bug.bug_id}")

        # Simulate action execution
        # In production, this would execute actual commands:
        # - Call Kubernetes API to restart pods
        # - Execute cache clearing commands
        # - Update configuration files
        # - Call service APIs for healing actions

        # For now, we simulate success for all actions
        await self._simulate_action_delay(action)

        logger.info(f"Successfully executed action: {action.action_type}")
        return True

    async def _simulate_action_delay(self, action: HealingAction) -> None:
        """
        Simulate action execution delay.

        Args:
            action: The action being executed
        """
        import asyncio
        # Simulate different execution times based on action complexity
        if action.risk_level == RiskLevel.LOW:
            await asyncio.sleep(0.1)
        elif action.risk_level == RiskLevel.MEDIUM:
            await asyncio.sleep(0.3)
        else:
            await asyncio.sleep(0.5)

    async def _update_bug_status(
        self,
        bug_id: str,
        success: bool,
        actions_taken: List[Dict[str, Any]]
    ) -> None:
        """
        Update bug status in database.

        Args:
            bug_id: Bug identifier
            success: Whether healing was successful
            actions_taken: List of actions that were taken
        """
        if not self.db:
            logger.warning("Database not initialized, skipping bug status update")
            return

        try:
            await self.db.bugs.update_one(
                {"bug_id": bug_id},
                {
                    "$set": {
                        "healing_attempted": True,
                        "healing_success": success,
                        "healing_actions": actions_taken,
                        "healing_timestamp": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Updated bug {bug_id} healing status")

        except Exception as e:
            logger.error(f"Failed to update bug status: {e}")

    async def _log_healing_attempt(
        self,
        bug_id: str,
        actions_taken: List[Dict[str, Any]],
        success: bool
    ) -> None:
        """
        Log healing attempt to database.

        Args:
            bug_id: Bug identifier
            actions_taken: Actions that were taken
            success: Whether healing was successful
        """
        if not self.db:
            return

        try:
            await self.db.healing_attempts.insert_one({
                "attempt_id": f"heal_{uuid.uuid4().hex[:12]}",
                "bug_id": bug_id,
                "actions_taken": actions_taken,
                "success": success,
                "attempted_at": datetime.utcnow()
            })
            logger.info(f"Logged healing attempt for bug {bug_id}")

        except Exception as e:
            logger.error(f"Failed to log healing attempt: {e}")

    async def get_healing_history(self, bug_id: str) -> List[Dict[str, Any]]:
        """
        Get healing history for a bug.

        Args:
            bug_id: Bug identifier

        Returns:
            List[Dict[str, Any]]: List of healing attempts
        """
        if not self.db:
            return []

        attempts = []
        cursor = self.db.healing_attempts.find({"bug_id": bug_id}).sort("attempted_at", -1)

        async for attempt in cursor:
            attempt.pop("_id", None)
            attempts.append(attempt)

        return attempts
