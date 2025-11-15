"""
GitHub integration service for automatic issue creation.
Creates detailed GitHub issues for detected bugs with AI analysis.
"""

import logging
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings
from app.models.bug import BugDetection

logger = logging.getLogger(__name__)


class GitHubService:
    """
    Service for integrating with GitHub.

    Provides automatic issue creation for detected bugs with detailed
    information including AI analysis and healing attempts.
    """

    def __init__(self):
        """Initialize the GitHub service."""
        self.token = settings.GITHUB_TOKEN
        self.repo = settings.GITHUB_REPO
        self.base_url = "https://api.github.com"

    def is_configured(self) -> bool:
        """
        Check if GitHub integration is configured.

        Returns:
            bool: True if GitHub token and repo are configured
        """
        return bool(self.token and self.repo)

    async def create_issue(
        self,
        bug: BugDetection,
        healing_result: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a GitHub issue for a detected bug.

        Args:
            bug: The detected bug
            healing_result: Optional healing attempt result

        Returns:
            Optional[Dict[str, Any]]: Created issue data or None if failed

        Raises:
            Exception: If issue creation fails
        """
        if not self.is_configured():
            logger.warning("GitHub integration not configured")
            return None

        try:
            # Prepare issue title
            title = f"[{bug.severity.value}] {bug.title}"

            # Prepare issue body
            body = self._format_issue_body(bug, healing_result)

            # Prepare labels
            labels = self._generate_labels(bug)

            # Create issue via GitHub API
            issue_data = {
                "title": title,
                "body": body,
                "labels": labels
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/repos/{self.repo}/issues",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Accept": "application/vnd.github.v3+json",
                        "Content-Type": "application/json"
                    },
                    json=issue_data
                )

                response.raise_for_status()
                issue = response.json()

            logger.info(f"Created GitHub issue #{issue['number']} for bug {bug.bug_id}")

            return {
                "issue_number": issue["number"],
                "issue_url": issue["html_url"],
                "issue_id": issue["id"]
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            raise

        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            raise

    def _format_issue_body(
        self,
        bug: BugDetection,
        healing_result: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format the GitHub issue body with bug details.

        Args:
            bug: The detected bug
            healing_result: Optional healing attempt result

        Returns:
            str: Formatted issue body in markdown
        """
        body_parts = [
            "## Bug Details",
            "",
            f"**Bug ID:** `{bug.bug_id}`",
            f"**Severity:** {bug.severity.value}",
            f"**Category:** {bug.category.value}",
            f"**Source Service:** {bug.source_service or 'Unknown'}",
            f"**Detected At:** {bug.detected_at.isoformat()}",
            f"**Confidence Score:** {bug.confidence_score}%",
            "",
            "## Description",
            "",
            bug.description,
            "",
            "## AI Analysis",
            "",
            bug.ai_analysis,
            ""
        ]

        # Add root cause if available
        if bug.root_cause:
            body_parts.extend([
                "## Root Cause",
                "",
                bug.root_cause,
                ""
            ])

        # Add recommended actions
        if bug.recommended_actions:
            body_parts.extend([
                "## Recommended Actions",
                ""
            ])
            for i, action in enumerate(bug.recommended_actions, 1):
                body_parts.append(f"{i}. {action}")
            body_parts.append("")

        # Add healing attempt information
        if healing_result:
            body_parts.extend([
                "## Self-Healing Attempt",
                "",
                f"**Status:** {'✅ Success' if healing_result.get('success') else '❌ Failed'}",
                f"**Message:** {healing_result.get('message', 'N/A')}",
                ""
            ])

            actions_taken = healing_result.get("actions_taken", [])
            if actions_taken:
                body_parts.extend([
                    "**Actions Taken:**",
                    ""
                ])
                for action in actions_taken:
                    status_emoji = "✅" if action.get("status") == "success" else "❌"
                    body_parts.append(
                        f"- {status_emoji} {action.get('description', action.get('action_type'))}"
                    )
                body_parts.append("")

            if healing_result.get("requires_approval"):
                body_parts.extend([
                    "> ⚠️ **Manual approval required for some healing actions**",
                    ""
                ])

        # Add footer
        body_parts.extend([
            "---",
            "",
            f"*Automatically generated by AI-Powered Bug Detection & Self-Healing System*",
            f"*Environment: {settings.ENV}*"
        ])

        return "\n".join(body_parts)

    def _generate_labels(self, bug: BugDetection) -> list:
        """
        Generate labels for the GitHub issue.

        Args:
            bug: The detected bug

        Returns:
            list: List of label names
        """
        labels = ["bug", "automated"]

        # Add severity label
        severity_label = f"severity:{bug.severity.value.lower()}"
        labels.append(severity_label)

        # Add category label
        category_label = f"category:{bug.category.value.lower()}"
        labels.append(category_label)

        # Add healing status label
        if bug.healing_attempted:
            if bug.healing_success:
                labels.append("auto-healed")
            else:
                labels.append("healing-failed")

        # Add environment label
        labels.append(f"env:{settings.ENV}")

        return labels

    async def add_comment(
        self,
        issue_number: int,
        comment: str
    ) -> Optional[Dict[str, Any]]:
        """
        Add a comment to an existing GitHub issue.

        Args:
            issue_number: Issue number
            comment: Comment text

        Returns:
            Optional[Dict[str, Any]]: Comment data or None if failed
        """
        if not self.is_configured():
            logger.warning("GitHub integration not configured")
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/repos/{self.repo}/issues/{issue_number}/comments",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Accept": "application/vnd.github.v3+json",
                        "Content-Type": "application/json"
                    },
                    json={"body": comment}
                )

                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to add comment to issue #{issue_number}: {e}")
            return None

    async def close_issue(
        self,
        issue_number: int,
        comment: Optional[str] = None
    ) -> bool:
        """
        Close a GitHub issue.

        Args:
            issue_number: Issue number
            comment: Optional closing comment

        Returns:
            bool: True if successful
        """
        if not self.is_configured():
            logger.warning("GitHub integration not configured")
            return False

        try:
            # Add comment if provided
            if comment:
                await self.add_comment(issue_number, comment)

            # Close the issue
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self.base_url}/repos/{self.repo}/issues/{issue_number}",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Accept": "application/vnd.github.v3+json",
                        "Content-Type": "application/json"
                    },
                    json={"state": "closed"}
                )

                response.raise_for_status()

            logger.info(f"Closed GitHub issue #{issue_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to close issue #{issue_number}: {e}")
            return False
