from typing import List, Optional, Dict
import re
from datetime import datetime

from app.models.tool import (
    Tool,
    ToolInstance,
    ToolStatus,
    ToolActivationRequest,
    ToolActivationResponse
)
from app.models.context import Context
from app.core.database import db

class MCPServer:
    def __init__(self):
        self.tool_collection = None
        self.instance_collection = None

    async def initialize(self):
        """Initialize MCP server with database collections."""
        self.tool_collection = db.get_db().tools
        self.instance_collection = db.get_db().tool_instances
        return self

    def _check_initialized(self):
        """Check if server is initialized."""
        if self.tool_collection is None or self.instance_collection is None:
            raise RuntimeError("MCP Server not initialized. Call initialize() first.")

    async def register_tool(self, tool: Tool) -> bool:
        """Register a new tool in the system."""
        self._check_initialized()
        try:
            await self.tool_collection.insert_one(tool.dict())
            return True
        except Exception as e:
            print(f"Error registering tool: {e}")
            return False

    async def discover_tools(self, context: Context) -> List[Tool]:
        """Discover relevant tools for a given context."""
        self._check_initialized()
        tools = []
        try:
            # Get all registered tools
            cursor = self.tool_collection.find({})
            all_tools = await cursor.to_list(length=None)
            
            for tool_data in all_tools:
                tool = Tool(**tool_data)
                
                # Check if tool matches context
                if self._tool_matches_context(tool, context):
                    tools.append(tool)
            
            return tools
        except Exception as e:
            print(f"Error discovering tools: {e}")
            return []

    def _tool_matches_context(self, tool: Tool, context: Context) -> bool:
        """Check if a tool matches the given context."""
        # Check content type matches capabilities
        if any(cap.value == context.content_type for cap in tool.capabilities):
            return True

        # Check context patterns
        for pattern in tool.context_patterns:
            if re.search(pattern, context.content, re.IGNORECASE):
                return True

        # Check activation rules
        for rule_key, rule_value in tool.activation_rules.items():
            if rule_key in context.metadata and context.metadata[rule_key] == rule_value:
                return True

        return False

    async def activate_tool(self, request: ToolActivationRequest) -> ToolActivationResponse:
        """Activate a tool for a specific context."""
        self._check_initialized()
        try:
            # Get tool
            tool_data = await self.tool_collection.find_one({"id": request.tool_id})
            if not tool_data:
                return ToolActivationResponse(
                    instance=ToolInstance(
                        tool_id=request.tool_id,
                        context_id=request.context_id,
                        status=ToolStatus.FAILED,
                        error_message="Tool not found"
                    ),
                    message="Tool not found",
                    success=False
                )

            tool = Tool(**tool_data)
            
            # Create tool instance
            instance = ToolInstance(
                tool_id=tool.id,
                context_id=request.context_id,
                status=ToolStatus.ACTIVE,
                activated_at=datetime.utcnow().isoformat(),
                resources={}  # Add resource allocation here
            )

            # Apply configuration override if provided
            config = request.configuration_override or tool.configuration
            
            # Store instance
            await self.instance_collection.insert_one(instance.dict())

            return ToolActivationResponse(
                instance=instance,
                message="Tool activated successfully",
                success=True
            )

        except Exception as e:
            return ToolActivationResponse(
                instance=ToolInstance(
                    tool_id=request.tool_id,
                    context_id=request.context_id,
                    status=ToolStatus.FAILED,
                    error_message=str(e)
                ),
                message=f"Error activating tool: {e}",
                success=False
            )

    async def deactivate_tool(self, tool_id: str, context_id: str) -> bool:
        """Deactivate a tool instance."""
        self._check_initialized()
        try:
            result = await self.instance_collection.update_one(
                {
                    "tool_id": tool_id,
                    "context_id": context_id,
                    "status": ToolStatus.ACTIVE
                },
                {
                    "$set": {
                        "status": ToolStatus.INACTIVE,
                        "deactivated_at": datetime.utcnow().isoformat()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error deactivating tool: {e}")
            return False

    async def get_active_tools(self, context_id: str) -> List[ToolInstance]:
        """Get all active tool instances for a context."""
        self._check_initialized()
        try:
            cursor = self.instance_collection.find({
                "context_id": context_id,
                "status": ToolStatus.ACTIVE
            })
            instances = await cursor.to_list(length=None)
            return [ToolInstance(**instance) for instance in instances]
        except Exception as e:
            print(f"Error getting active tools: {e}")
            return []

mcp_server = MCPServer()
