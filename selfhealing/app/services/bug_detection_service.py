"""
Bug detection service using AI-powered analysis with OpenRouter/Claude.
Provides intelligent log analysis and bug detection capabilities.
"""

import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings
from app.core.database import get_database
from app.models.bug import (
    BugDetection,
    BugSeverity,
    BugCategory,
    LogEntry,
    AnalysisRequest
)

logger = logging.getLogger(__name__)


class BugDetectionService:
    """
    Service for detecting bugs using AI-powered analysis.

    Uses OpenRouter API with Claude 3.5 Sonnet for intelligent log analysis
    and bug detection, with rule-based fallback detection.
    """

    def __init__(self):
        """Initialize the bug detection service."""
        self.base_url = settings.OPENROUTER_BASE_URL
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.AI_MODEL
        self.db = None

    async def initialize(self):
        """Initialize database connection."""
        self.db = await get_database()

    async def analyze_logs(self, request: AnalysisRequest) -> List[BugDetection]:
        """
        Analyze logs for potential bugs using AI.

        Args:
            request: Analysis request containing logs to analyze

        Returns:
            List[BugDetection]: List of detected bugs

        Raises:
            Exception: If analysis fails
        """
        try:
            logger.info(f"Analyzing {len(request.logs)} log entries")

            # Try AI-powered analysis first
            try:
                bugs = await self._analyze_with_ai(request)
                logger.info(f"AI analysis detected {len(bugs)} bugs")
            except Exception as e:
                logger.warning(f"AI analysis failed: {e}, falling back to rule-based detection")
                bugs = await self._rule_based_detection(request)
                logger.info(f"Rule-based detection found {len(bugs)} bugs")

            # Store detected bugs in database
            if bugs and self.db:
                for bug in bugs:
                    await self._store_bug(bug)

            return bugs

        except Exception as e:
            logger.error(f"Log analysis failed: {e}")
            raise

    async def _analyze_with_ai(self, request: AnalysisRequest) -> List[BugDetection]:
        """
        Analyze logs using OpenRouter AI (Claude 3.5 Sonnet).

        Args:
            request: Analysis request containing logs

        Returns:
            List[BugDetection]: Detected bugs from AI analysis

        Raises:
            Exception: If AI API call fails
        """
        # Prepare log context for AI
        log_context = self._prepare_log_context(request)

        # Create the AI prompt
        system_prompt = """You are an expert system administrator and DevOps engineer specializing in bug detection and root cause analysis.

Analyze the provided logs and identify any bugs, errors, or issues. For each bug detected, provide:
1. A clear title
2. Detailed description
3. Severity level (CRITICAL, HIGH, MEDIUM, LOW, INFO)
4. Category (DATABASE, MEMORY, NETWORK, DISK, APPLICATION, SECURITY)
5. Root cause analysis
6. Recommended actions to fix the issue
7. Confidence score (0-100) for your analysis

Return your analysis as a JSON array of bug objects. If no bugs are found, return an empty array."""

        user_prompt = f"""Analyze these logs and identify any bugs or issues:

Service: {request.service_name or 'Unknown'}
Time Range: {request.time_range or 'Not specified'}

Logs:
{log_context}

Return ONLY a JSON array of bug objects with this structure:
[
  {{
    "title": "Bug title",
    "description": "Detailed description",
    "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
    "category": "DATABASE|MEMORY|NETWORK|DISK|APPLICATION|SECURITY",
    "root_cause": "Root cause explanation",
    "recommended_actions": ["action1", "action2"],
    "ai_analysis": "Your detailed analysis",
    "confidence_score": 85
  }}
]"""

        # Call OpenRouter API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": settings.AI_TEMPERATURE,
                    "max_tokens": settings.AI_MAX_TOKENS,
                }
            )

            response.raise_for_status()
            result = response.json()

        # Extract AI response
        ai_response = result["choices"][0]["message"]["content"]

        # Parse AI response
        bugs = self._parse_ai_response(ai_response, request.service_name)

        return bugs

    def _prepare_log_context(self, request: AnalysisRequest) -> str:
        """
        Prepare log entries for AI analysis.

        Args:
            request: Analysis request containing logs

        Returns:
            str: Formatted log context
        """
        log_lines = []
        for log in request.logs:
            metadata_str = ""
            if log.metadata:
                metadata_str = f" | {json.dumps(log.metadata)}"

            log_lines.append(
                f"[{log.timestamp}] [{log.level}] [{log.service}] {log.message}{metadata_str}"
            )

        return "\n".join(log_lines)

    def _parse_ai_response(
        self,
        ai_response: str,
        service_name: Optional[str]
    ) -> List[BugDetection]:
        """
        Parse AI response into BugDetection objects.

        Args:
            ai_response: Raw AI response text
            service_name: Source service name

        Returns:
            List[BugDetection]: Parsed bug detections
        """
        bugs = []

        try:
            # Extract JSON from response (might be wrapped in markdown code blocks)
            json_str = ai_response.strip()
            if json_str.startswith("```"):
                # Remove markdown code blocks
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1]) if len(lines) > 2 else json_str

            # Parse JSON
            bug_data_list = json.loads(json_str)

            if not isinstance(bug_data_list, list):
                bug_data_list = [bug_data_list]

            for bug_data in bug_data_list:
                bug = BugDetection(
                    bug_id=f"bug_{uuid.uuid4().hex[:12]}",
                    title=bug_data.get("title", "Unknown Bug"),
                    description=bug_data.get("description", ""),
                    severity=BugSeverity(bug_data.get("severity", "MEDIUM")),
                    category=BugCategory(bug_data.get("category", "APPLICATION")),
                    ai_analysis=bug_data.get("ai_analysis", ""),
                    root_cause=bug_data.get("root_cause"),
                    recommended_actions=bug_data.get("recommended_actions", []),
                    confidence_score=float(bug_data.get("confidence_score", 50.0)),
                    source_service=service_name,
                    detected_at=datetime.utcnow()
                )
                bugs.append(bug)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            # Create a generic bug if parsing fails
            bugs.append(self._create_generic_bug(ai_response, service_name))

        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            bugs.append(self._create_generic_bug(ai_response, service_name))

        return bugs

    def _create_generic_bug(
        self,
        ai_response: str,
        service_name: Optional[str]
    ) -> BugDetection:
        """
        Create a generic bug detection from unparseable AI response.

        Args:
            ai_response: AI response text
            service_name: Source service name

        Returns:
            BugDetection: Generic bug detection
        """
        return BugDetection(
            bug_id=f"bug_{uuid.uuid4().hex[:12]}",
            title="Issues Detected in Logs",
            description="AI detected potential issues but response format was unexpected",
            severity=BugSeverity.MEDIUM,
            category=BugCategory.APPLICATION,
            ai_analysis=ai_response[:1000],  # Truncate to avoid huge responses
            confidence_score=50.0,
            source_service=service_name,
            detected_at=datetime.utcnow()
        )

    async def _rule_based_detection(self, request: AnalysisRequest) -> List[BugDetection]:
        """
        Fallback rule-based bug detection.

        Args:
            request: Analysis request containing logs

        Returns:
            List[BugDetection]: Detected bugs using rule-based approach
        """
        bugs = []
        error_patterns = {
            "database": {
                "keywords": ["database", "sql", "connection pool", "deadlock", "timeout"],
                "category": BugCategory.DATABASE,
                "severity": BugSeverity.HIGH
            },
            "memory": {
                "keywords": ["out of memory", "memory leak", "heap", "oom"],
                "category": BugCategory.MEMORY,
                "severity": BugSeverity.CRITICAL
            },
            "network": {
                "keywords": ["connection refused", "timeout", "network", "socket"],
                "category": BugCategory.NETWORK,
                "severity": BugSeverity.HIGH
            },
            "security": {
                "keywords": ["unauthorized", "forbidden", "authentication", "sql injection"],
                "category": BugCategory.SECURITY,
                "severity": BugSeverity.CRITICAL
            }
        }

        error_logs = [log for log in request.logs if log.level in ["ERROR", "CRITICAL", "FATAL"]]

        for log in error_logs:
            message_lower = log.message.lower()

            for pattern_name, pattern_info in error_patterns.items():
                if any(keyword in message_lower for keyword in pattern_info["keywords"]):
                    bug = BugDetection(
                        bug_id=f"bug_{uuid.uuid4().hex[:12]}",
                        title=f"{pattern_name.title()} Issue Detected",
                        description=f"Error log detected: {log.message}",
                        severity=pattern_info["severity"],
                        category=pattern_info["category"],
                        ai_analysis=f"Rule-based detection identified {pattern_name} issue in logs",
                        root_cause=f"Detected based on error pattern matching in log: {log.message}",
                        recommended_actions=[
                            f"Investigate {pattern_name} subsystem",
                            "Check service health and metrics",
                            "Review recent changes"
                        ],
                        confidence_score=70.0,
                        source_service=request.service_name or log.service,
                        detected_at=datetime.utcnow()
                    )
                    bugs.append(bug)
                    break  # Only create one bug per error log

        return bugs

    async def _store_bug(self, bug: BugDetection) -> None:
        """
        Store detected bug in database.

        Args:
            bug: Bug detection to store
        """
        try:
            if not self.db:
                logger.warning("Database not initialized, skipping bug storage")
                return

            bug_dict = bug.model_dump()
            bug_dict["severity"] = bug.severity.value
            bug_dict["category"] = bug.category.value

            await self.db.bugs.insert_one(bug_dict)
            logger.info(f"Stored bug {bug.bug_id} in database")

        except Exception as e:
            logger.error(f"Failed to store bug in database: {e}")

    async def get_bug(self, bug_id: str) -> Optional[BugDetection]:
        """
        Retrieve a bug by ID.

        Args:
            bug_id: Bug identifier

        Returns:
            Optional[BugDetection]: Bug if found, None otherwise
        """
        if not self.db:
            return None

        bug_doc = await self.db.bugs.find_one({"bug_id": bug_id})
        if not bug_doc:
            return None

        bug_doc.pop("_id", None)
        return BugDetection(**bug_doc)

    async def list_bugs(
        self,
        page: int = 1,
        page_size: int = 50,
        severity: Optional[BugSeverity] = None
    ) -> List[BugDetection]:
        """
        List bugs with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of bugs per page
            severity: Optional severity filter

        Returns:
            List[BugDetection]: List of bugs
        """
        if not self.db:
            return []

        query = {}
        if severity:
            query["severity"] = severity.value

        skip = (page - 1) * page_size

        cursor = self.db.bugs.find(query).sort("detected_at", -1).skip(skip).limit(page_size)
        bugs = []

        async for bug_doc in cursor:
            bug_doc.pop("_id", None)
            bugs.append(BugDetection(**bug_doc))

        return bugs
