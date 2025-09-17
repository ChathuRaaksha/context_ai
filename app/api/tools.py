from fastapi import APIRouter, HTTPException
from typing import List, Optional

from app.models.tool import (
    Tool,
    ToolMetadata,
    ToolInstance,
    ToolStatus,
    ToolConfiguration,
    ResourceRequirement
)
from app.services.tool_service import tool_service

router = APIRouter(prefix="/tools", tags=["tools"])

@router.post("/register", response_model=Tool)
async def register_tool(
    tool_data: dict
):
    """Register a new tool with the system."""
    try:
        metadata = ToolMetadata(**tool_data["metadata"])
        requirements = ResourceRequirement(**tool_data.get("requirements", {}))
        configuration = ToolConfiguration(**tool_data.get("configuration", {}))
        
        tool = await tool_service.register_tool(
            metadata=metadata,
            capabilities=tool_data["capabilities"],
            requirements=requirements,
            configuration=configuration,
            context_patterns=tool_data.get("context_patterns", []),
            activation_rules=tool_data.get("activation_rules", {})
        )
        return tool
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{tool_id}/activate/{context_id}")
async def activate_tool(
    tool_id: str,
    context_id: str,
    configuration: Optional[ToolConfiguration] = None
):
    """Activate a tool for a specific context."""
    response = await tool_service.activate_tool(
        tool_id=tool_id,
        context_id=context_id,
        configuration_override=configuration
    )
    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)
    return response

@router.post("/{tool_id}/deactivate/{context_id}")
async def deactivate_tool(tool_id: str, context_id: str):
    """Deactivate a tool for a specific context."""
    success = await tool_service.deactivate_tool(tool_id, context_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to deactivate tool")
    return {"message": "Tool deactivated successfully"}

@router.get("/active/{context_id}", response_model=List[ToolInstance])
async def get_active_tools(context_id: str):
    """Get all active tools for a context."""
    return await tool_service.get_active_tools(context_id)

@router.patch("/{tool_id}/status/{context_id}")
async def update_tool_status(
    tool_id: str,
    context_id: str,
    status: ToolStatus,
    error_message: Optional[str] = None
):
    """Update the status of a tool instance."""
    success = await tool_service.update_tool_status(
        tool_id=tool_id,
        context_id=context_id,
        status=status,
        error_message=error_message
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update tool status")
    return {"message": "Tool status updated successfully"}
