import asyncio
import nest_asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import db
from app.services.tool_service import tool_service
from app.services.context_service import context_service

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Store original lifespan
original_lifespan = app.router.lifespan_context

@asynccontextmanager
async def test_lifespan(app: FastAPI):
    """Test-specific lifespan that ensures database and services are initialized."""
    # Initialize services
    await db.connect_db()
    await tool_service.initialize()
    await context_service.initialize()
    
    try:
        # Run the original lifespan
        async with original_lifespan(app):
            yield
    finally:
        # Cleanup
        await db.close_db()

# Replace the app's lifespan with our test lifespan
app.router.lifespan_context = test_lifespan

# Create test client with the modified app
client = TestClient(app)

def test_register_tool():
    """Test tool registration."""
    print("\n=== Testing Tool Registration ===")
    tool_data = {
        "metadata": {
            "name": "Documentation Analyzer",
            "version": "1.0.0",
            "description": "Analyzes and improves documentation content",
            "vendor": "Internal",
            "documentation_url": "http://example.com/docs",
            "tags": ["documentation", "analysis"]
        },
        "capabilities": ["documentation"],
        "requirements": {
            "cpu": "1",
            "memory": "512Mi",
            "permissions": ["read", "write"]
        },
        "configuration": {
            "enabled": True,
            "auto_activate": True,
            "priority": 1,
            "timeout_seconds": 30
        },
        "context_patterns": [".*documentation.*", ".*guide.*", ".*manual.*"],
        "activation_rules": {
            "content_type": "documentation"
        }
    }
    
    with client as c:
        response = c.post("/api/tools/register", json=tool_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.status_code == 200 else response.text}")
        return response.json()["id"] if response.status_code == 200 else None

def test_create_context(tool_id: str):
    """Test context creation and tool activation."""
    print("\n=== Testing Context Creation with Auto Tool Activation ===")
    context_data = {
        "content": "This is a documentation guide for the context management system.",
        "content_type": "documentation",
        "tags": ["guide", "documentation"],
        "metadata": {
            "author": "test",
            "version": "1.0"
        }
    }

    with client as c:
        response = c.post("/api/contexts/", json=context_data)
        print("\nCreating Context:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.status_code == 200 else response.text}")
        
        if response.status_code == 200 or response.status_code == 201:
            context_id = response.json()["id"]
            # Get active tools for the context
            tools_response = c.get(f"/api/tools/active/{context_id}")
            print("\nActive Tools:")
            print(f"Status Code: {tools_response.status_code}")
            print(f"Response: {tools_response.json() if tools_response.status_code == 200 else tools_response.text}")
            
            # Verify if our tool was activated
            if tools_response.status_code == 200:
                active_tools = tools_response.json()
                active_tool_ids = [tool["tool_id"] for tool in active_tools]
                if tool_id in active_tool_ids:
                    print(f"\nSuccess: Tool {tool_id} was automatically activated!")
                else:
                    print(f"\nWarning: Tool {tool_id} was not activated as expected.")

def run_tests():
    """Run all tests."""
    with client:  # This will handle the lifespan context
        tool_id = test_register_tool()
        if tool_id:
            test_create_context(tool_id)

if __name__ == "__main__":
    run_tests()
