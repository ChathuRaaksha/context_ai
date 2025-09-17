from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.models.context import (
    ContextCreate,
    ContextUpdate,
    ContextResponse,
    ContextSearch,
    ContextImprovement,
    ContentType
)
from app.services.context_service import context_service

router = APIRouter(prefix="/contexts", tags=["contexts"])

@router.post("/", response_model=ContextResponse, status_code=201)
async def create_context(context: ContextCreate):
    """Create a new context."""
    try:
        return await context_service.create_context(context)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{context_id}", response_model=ContextResponse)
async def get_context(context_id: str):
    """Get a specific context by ID."""
    context = await context_service.get_context(context_id)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    return context

@router.put("/{context_id}", response_model=ContextResponse)
async def update_context(context_id: str, context: ContextUpdate):
    """Update an existing context."""
    updated = await context_service.update_context(context_id, context)
    if not updated:
        raise HTTPException(status_code=404, detail="Context not found")
    return updated

@router.delete("/{context_id}", status_code=204)
async def delete_context(context_id: str):
    """Delete a context."""
    deleted = await context_service.delete_context(context_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Context not found")
    return None

@router.get("/", response_model=List[ContextResponse])
async def search_contexts(
    query: Optional[str] = Query(None, description="Search query"),
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    min_quality: Optional[float] = Query(None, ge=0, le=1, description="Minimum quality score")
):
    """Search for contexts with various filters."""
    search = ContextSearch(
        query=query or "",
        content_type=content_type,
        tags=tags,
        min_quality=min_quality
    )
    return await context_service.search_contexts(search)

@router.post("/{context_id}/improve", response_model=ContextResponse)
async def improve_context(context_id: str):
    """Improve a context using LLM."""
    improved = await context_service.improve_context(context_id)
    if not improved:
        raise HTTPException(status_code=404, detail="Context not found")
    return improved
