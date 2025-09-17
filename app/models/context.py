from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from app.models.tool import ToolInstance

class ContentType(str, Enum):
    DOCUMENTATION = "documentation"
    INFRASTRUCTURE = "infrastructure"
    AI_TOOLS = "ai_tools"

class QualityMetrics(BaseModel):
    completeness: float = Field(ge=0, le=1)
    accuracy: float = Field(ge=0, le=1)
    relevance: float = Field(ge=0, le=1)
    clarity: float = Field(ge=0, le=1)

class Context(BaseModel):
    content: str
    content_type: ContentType
    metadata: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    quality_metrics: Optional[QualityMetrics] = None
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    parent_id: Optional[str] = None
    references: List[str] = Field(default_factory=list)

class ContextCreate(BaseModel):
    content: str
    content_type: ContentType
    metadata: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

class ContextUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None
    quality_metrics: Optional[QualityMetrics] = None

class ContextResponse(Context):
    id: str
    active_tools: List[ToolInstance] = Field(default_factory=list)

class ContextSearch(BaseModel):
    query: str
    content_type: Optional[ContentType] = None
    tags: Optional[List[str]] = None
    min_quality: Optional[float] = Field(None, ge=0, le=1)

class ContextImprovement(BaseModel):
    context_id: str
    suggestions: List[str]
    improved_content: Optional[str] = None
    quality_delta: Optional[float] = None

class ContextWithTools(BaseModel):
    context: ContextResponse
    tools: List[ToolInstance]
    tool_capabilities: List[str]
    tool_count: int

    @classmethod
    def from_context(cls, context: ContextResponse):
        return cls(
            context=context,
            tools=context.active_tools,
            tool_capabilities=[tool.tool_id for tool in context.active_tools],
            tool_count=len(context.active_tools)
        )
