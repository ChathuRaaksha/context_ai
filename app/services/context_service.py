from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from app.core.database import db
from app.models.context import (
    Context,
    ContextCreate,
    ContextUpdate,
    ContextResponse,
    ContextSearch,
    QualityMetrics
)
from app.services.llm_service import llm_service
from app.services.tool_service import tool_service

class ContextService:
    def __init__(self):
        self.collection = None

    async def initialize(self):
        self.collection = db.get_db().contexts
        return self

    def _check_initialized(self):
        if self.collection is None:
            raise RuntimeError("ContextService not initialized. Call initialize() first.")

    async def create_context(self, context_data: ContextCreate) -> ContextResponse:
        self._check_initialized()
        # Extract metadata and suggest tags using LLM
        metadata = await llm_service.extract_metadata(context_data.content)
        suggested_tags = await llm_service.suggest_tags(context_data.content)
        
        # Create context object with initial quality metrics
        context_dict = context_data.dict()
        context_dict["metadata"].update(metadata)
        context_dict["tags"] = list(set(context_data.tags + suggested_tags))
        context_dict["quality_metrics"] = QualityMetrics(
            completeness=0.0,
            accuracy=0.0,
            relevance=0.0,
            clarity=0.0
        )
        context = Context(**context_dict)
        
        # Assess quality using LLM
        quality_metrics = await llm_service.assess_quality(context)
        context.quality_metrics = quality_metrics

        # Insert into database
        result = await self.collection.insert_one(context.dict())
        context_id = str(result.inserted_id)
        
        # Auto-discover and activate relevant tools
        active_tools = await tool_service.auto_discover_and_activate(context)
        
        # Return response with ID
        return ContextResponse(
            id=context_id,
            **context.dict(),
            active_tools=[tool.dict() for tool in active_tools]
        )

    async def get_context(self, context_id: str) -> Optional[ContextResponse]:
        self._check_initialized()
        result = await self.collection.find_one({"_id": ObjectId(context_id)})
        if result:
            # Get active tools for the context
            active_tools = await tool_service.get_active_tools(context_id)
            return ContextResponse(
                id=str(result["_id"]),
                **result,
                active_tools=[tool.dict() for tool in active_tools]
            )
        return None

    async def update_context(self, context_id: str, update_data: ContextUpdate) -> Optional[ContextResponse]:
        self._check_initialized()
        # Get existing context
        existing = await self.get_context(context_id)
        if not existing:
            return None

        # Prepare update data
        update_dict = update_data.dict(exclude_unset=True)
        
        if "content" in update_dict:
            # If content is updated, re-assess quality and metadata
            metadata = await llm_service.extract_metadata(update_dict["content"])
            suggested_tags = await llm_service.suggest_tags(update_dict["content"])
            
            # Merge existing and new tags
            if "tags" in update_dict:
                update_dict["tags"] = list(set(update_dict["tags"] + suggested_tags))
            else:
                update_dict["tags"] = list(set(existing.tags + suggested_tags))
            
            update_dict["metadata"] = metadata
            update_dict["version"] = existing.version + 1
            
            # Create temporary context for quality assessment
            temp_context = Context(
                content=update_dict["content"],
                content_type=existing.content_type,
                tags=update_dict["tags"],
                metadata=metadata,
                quality_metrics=existing.quality_metrics,
                version=update_dict["version"]
            )
            
            # Assess new quality
            update_dict["quality_metrics"] = (await llm_service.assess_quality(temp_context)).dict()
            
            # Re-evaluate tools based on updated content
            await self._update_tools_for_context(temp_context, context_id)

        update_dict["updated_at"] = datetime.utcnow()

        # Update in database
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(context_id)},
            {"$set": update_dict},
            return_document=True
        )

        if result:
            # Get updated active tools
            active_tools = await tool_service.get_active_tools(context_id)
            return ContextResponse(
                id=str(result["_id"]),
                **result,
                active_tools=[tool.dict() for tool in active_tools]
            )
        return None

    async def _update_tools_for_context(self, context: Context, context_id: str):
        """Update tool activations based on context changes."""
        # Get current active tools
        current_tools = await tool_service.get_active_tools(context_id)
        current_tool_ids = {tool.tool_id for tool in current_tools}
        
        # Discover tools that should be active
        discovered_tools = await tool_service.discover_tools_for_context(context)
        discovered_tool_ids = {tool.id for tool in discovered_tools}
        
        # Deactivate tools that are no longer relevant
        for tool in current_tools:
            if tool.tool_id not in discovered_tool_ids:
                await tool_service.deactivate_tool(tool.tool_id, context_id)
        
        # Activate newly discovered tools
        for tool in discovered_tools:
            if tool.id not in current_tool_ids and tool.configuration.auto_activate:
                await tool_service.activate_tool(tool.id, context_id)

    async def delete_context(self, context_id: str) -> bool:
        self._check_initialized()
        # Deactivate all tools for the context
        active_tools = await tool_service.get_active_tools(context_id)
        for tool in active_tools:
            await tool_service.deactivate_tool(tool.tool_id, context_id)
        
        # Delete the context
        result = await self.collection.delete_one({"_id": ObjectId(context_id)})
        return result.deleted_count > 0

    async def search_contexts(self, search: ContextSearch) -> List[ContextResponse]:
        self._check_initialized()
        # Build query
        query = {}
        if search.content_type:
            query["content_type"] = search.content_type
        if search.tags:
            query["tags"] = {"$all": search.tags}
        if search.min_quality:
            query["quality_metrics.completeness"] = {"$gte": search.min_quality}
            query["quality_metrics.accuracy"] = {"$gte": search.min_quality}
            query["quality_metrics.relevance"] = {"$gte": search.min_quality}
            query["quality_metrics.clarity"] = {"$gte": search.min_quality}

        # Text search
        if search.query:
            query["$text"] = {"$search": search.query}

        # Execute search
        cursor = self.collection.find(query)
        results = await cursor.to_list(length=None)
        
        # Get active tools for each context
        contexts = []
        for doc in results:
            context_id = str(doc["_id"])
            active_tools = await tool_service.get_active_tools(context_id)
            contexts.append(
                ContextResponse(
                    id=context_id,
                    **doc,
                    active_tools=[tool.dict() for tool in active_tools]
                )
            )
        return contexts

    async def improve_context(self, context_id: str) -> Optional[ContextResponse]:
        self._check_initialized()
        # Get existing context
        context = await self.get_context(context_id)
        if not context:
            return None

        # Get improvement suggestions
        improvement = await llm_service.improve_context(context)
        
        # Update context with improvements
        if improvement.improved_content:
            update_data = ContextUpdate(
                content=improvement.improved_content
            )
            return await self.update_context(context_id, update_data)
        
        return context

context_service = ContextService()
