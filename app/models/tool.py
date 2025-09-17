from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class ToolCapability(str, Enum):
    DOCUMENTATION = "documentation"
    CODE_ANALYSIS = "code_analysis"
    INFRASTRUCTURE = "infrastructure"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"

class ResourceRequirement(BaseModel):
    cpu: Optional[str] = None
    memory: Optional[str] = None
    storage: Optional[str] = None
    api_key: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)

class ToolMetadata(BaseModel):
    name: str
    version: str
    description: str
    vendor: Optional[str] = None
    documentation_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class ToolConfiguration(BaseModel):
    enabled: bool = True
    auto_activate: bool = False
    priority: int = 1
    timeout_seconds: int = 30
    retry_count: int = 3
    cache_ttl_seconds: int = 300

class Tool(BaseModel):
    id: str
    metadata: ToolMetadata
    capabilities: List[ToolCapability]
    requirements: ResourceRequirement
    configuration: ToolConfiguration
    context_patterns: List[str] = Field(default_factory=list)
    activation_rules: Dict[str, str] = Field(default_factory=dict)

class ToolStatus(str, Enum):
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"

class ToolInstance(BaseModel):
    tool_id: str
    context_id: str
    status: ToolStatus
    activated_at: Optional[str] = None
    deactivated_at: Optional[str] = None
    error_message: Optional[str] = None
    resources: Dict[str, str] = Field(default_factory=dict)

class ToolActivationRequest(BaseModel):
    tool_id: str
    context_id: str
    configuration_override: Optional[ToolConfiguration] = None

class ToolActivationResponse(BaseModel):
    instance: ToolInstance
    message: str
    success: bool
