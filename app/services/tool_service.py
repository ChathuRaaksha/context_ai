from typing import List, Optional
from datetime import datetime
import uuid

from app.core.mcp import mcp_server
from app.models.tool import (
    Tool,
    ToolMetadata,
    ToolInstance,
    ToolStatus,
    ToolActivationRequest,
    ToolActivationResponse,
    ResourceRequirement,
    ToolConfiguration
)
from app.models.context import Context

class ToolService:
    def __init__(self):
        self.initialized = False

    async def initialize(self):
        """Initialize the tool service."""
        if not self.initialized:
            await mcp_server.initialize()
            self.initialized = True
        return self

    async def _ensure_initialized(self):
        """Ensure the service is initialized."""
        if not self.initialized:
            await self.initialize()

    async def register_tool(
        self,
        metadata: ToolMetadata,
        capabilities: List[str],
        requirements: Optional[ResourceRequirement] = None,
        configuration: Optional[ToolConfiguration] = None,
        context_patterns: Optional[List[str]] = None,
        activation_rules: Optional[dict] = None
    ) -> Tool:
        """Register a new tool with the system."""
        await self._ensure_initialized()
        tool = Tool(
            id=str(uuid.uuid4()),
            metadata=metadata,
            capabilities=capabilities,
            requirements=requirements or ResourceRequirement(),
            configuration=configuration or ToolConfiguration(),
            context_patterns=context_patterns or [],
            activation_rules=activation_rules or {}
        )

        success = await mcp_server.register_tool(tool)
        if not success:
            raise Exception("Failed to register tool")
        
        return tool

    async def discover_tools_for_context(self, context: Context) -> List[Tool]:
        """Discover tools that are relevant for a given context."""
        await self._ensure_initialized()
        return await mcp_server.discover_tools(context)

    async def activate_tool(
        self,
        tool_id: str,
        context_id: str,
        configuration_override: Optional[ToolConfiguration] = None
    ) -> ToolActivationResponse:
        """Activate a tool for a specific context."""
        await self._ensure_initialized()
        request = ToolActivationRequest(
            tool_id=tool_id,
            context_id=context_id,
            configuration_override=configuration_override
        )
        return await mcp_server.activate_tool(request)

    async def deactivate_tool(self, tool_id: str, context_id: str) -> bool:
        """Deactivate a tool for a specific context."""
        await self._ensure_initialized()
        return await mcp_server.deactivate_tool(tool_id, context_id)

    async def get_active_tools(self, context_id: str) -> List[ToolInstance]:
        """Get all active tools for a context."""
        await self._ensure_initialized()
        return await mcp_server.get_active_tools(context_id)

    async def auto_discover_and_activate(self, context: Context) -> List[ToolInstance]:
        """Automatically discover and activate relevant tools for a context."""
        await self._ensure_initialized()
        active_tools = []
        
        # Discover relevant tools
        tools = await self.discover_tools_for_context(context)
        
        # Activate auto-activate tools
        for tool in tools:
            if tool.configuration.auto_activate:
                response = await self.activate_tool(tool.id, str(context.id))
                if response.success:
                    active_tools.append(response.instance)
        
        return active_tools

    async def update_tool_status(
        self,
        tool_id: str,
        context_id: str,
        status: ToolStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """Update the status of a tool instance."""
        await self._ensure_initialized()
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            result = await mcp_server.instance_collection.update_one(
                {
                    "tool_id": tool_id,
                    "context_id": context_id
                },
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating tool status: {e}")
            return False

tool_service = ToolService()
