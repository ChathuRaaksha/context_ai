import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import db
from app.services.tool_service import tool_service
from app.services.context_service import context_service

# Store tool_id for tests
test_tool_id = None

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Setup database connection before each test."""
    await db.connect_db()
    await tool_service.initialize()
    await context_service.initialize()
    yield
    if db.client:
        await db.close_db()

@pytest_asyncio.fixture
async def async_client():
    """Create async client for testing."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        yield client

@pytest_asyncio.fixture
async def tool_id(async_client):
    """Create a tool and return its ID for testing."""
    global test_tool_id
    if test_tool_id is None:
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
        response = await async_client.post("/api/tools/register", json=tool_data)
        if response.status_code == 200:
            test_tool_id = response.json()["id"]
    return test_tool_id

@pytest.mark.asyncio
async def test_register_tool(async_client):
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
    
    response = await async_client.post("/api/tools/register", json=tool_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json() if response.status_code == 200 else response.text}")
    return response.json()["id"] if response.status_code == 200 else None

@pytest.mark.asyncio
async def test_create_context(async_client, tool_id: str):
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

    response = await async_client.post("/api/contexts/", json=context_data)
    print("\nCreating Context:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json() if response.status_code == 200 else response.text}")
    
    if response.status_code == 200 or response.status_code == 201:
        context_id = response.json()["id"]
        # Get active tools for the context
        tools_response = await async_client.get(f"/api/tools/active/{context_id}")
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

@pytest.mark.asyncio
async def test_employment_contract_workflow(async_client):
    """Test the employment contract context workflow."""
    print("\n=== Testing Employment Contract Workflow ===")
    
    # 1. Register contract generation tool
    contract_tool_data = {
        "metadata": {
            "name": "Employment Contract Generator",
            "version": "1.0.0",
            "description": "Generates and customizes employment contracts",
            "vendor": "Internal",
            "documentation_url": "http://example.com/contract-docs",
            "tags": ["contracts", "legal", "employment"]
        },
        "capabilities": ["contract_generation", "legal_compliance"],
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
        "context_patterns": [".*employment.*", ".*contract.*", ".*legal.*"],
        "activation_rules": {
            "content_type": "ai_tools"
        }
    }
    
    # Register tool
    tool_response = await async_client.post("/api/tools/register", json=contract_tool_data)
    print(f"Tool Registration Status: {tool_response.status_code}")
    tool_id = tool_response.json()["id"] if tool_response.status_code == 200 else None
    
    if not tool_id:
        print("Failed to register contract tool")
        return
        
    # 2. Create employment contract context
    contract_context = {
        "content": """Generate a standard employment contract including:
        - Job role and responsibilities
        - Salary and benefits
        - Start date
        - Working hours
        - Termination clauses
        - Compliance with Swedish labour laws""",
        "content_type": "ai_tools",
        "tags": ["employment", "contract", "legal", "swedish"],
        "metadata": {
            "locale": "sv-SE",
            "type": "employment_contract",
            "version": "1.0"
        }
    }
    
    context_response = await async_client.post("/api/contexts/", json=contract_context)
    print("\nContext Creation Status:", context_response.status_code)
    
    if context_response.status_code != 200:
        print("Failed to create context")
        return
        
    context_id = context_response.json()["id"]
    
    # 3. Test context search
    search_data = {
        "query": "employment contract",
        "content_type": "ai_tools",
        "tags": ["swedish"]
    }
    
    search_response = await async_client.post("/api/contexts/search", json=search_data)
    print("\nSearch Results Status:", search_response.status_code)
    if search_response.status_code == 200:
        results = search_response.json()
        print(f"Found {len(results)} matching contexts")
        
    # 4. Test context improvement
    improve_response = await async_client.post(f"/api/contexts/{context_id}/improve")
    print("\nContext Improvement Status:", improve_response.status_code)
    if improve_response.status_code == 200:
        improved_context = improve_response.json()
        print("Context improved successfully")
        
    # 5. Verify active tools
    tools_response = await async_client.get(f"/api/tools/active/{context_id}")
    print("\nActive Tools Status:", tools_response.status_code)
    if tools_response.status_code == 200:
        active_tools = tools_response.json()
        print(f"Number of active tools: {len(active_tools)}")
        
        # Verify our contract tool was activated
        active_tool_ids = [tool["tool_id"] for tool in active_tools]
        if tool_id in active_tool_ids:
            print(f"Success: Contract tool {tool_id} was automatically activated!")
        else:
            print(f"Warning: Contract tool {tool_id} was not activated as expected.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
