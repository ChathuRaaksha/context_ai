# Context Management System

An AI-powered context management system for documentation and infrastructure, built with FastAPI and MongoDB.

## Features

- Context Management with AI-powered analysis
- Tool Integration via Model Context Protocol (MCP)
- Automatic Tool Discovery and Activation
- Quality Assessment of Context
- RESTful API Interface

## Prerequisites

- Python 3.10+
- MongoDB
- Node.js (for frontend)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ChathuRaaksha/contextai.git
cd contextai/context-management-python
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with:
```
MONGODB_URI=your_mongodb_uri
OPENROUTER_API_KEY=your_api_key
OPENROUTER_BASE_URL=your_base_url
```

## Running the Application

1. Start the server:
```bash
uvicorn app.main:app --reload --port 8002
```

2. Access the API documentation:
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

## API Endpoints

### Contexts
- `POST /api/contexts/` - Create a new context
- `GET /api/contexts/{context_id}` - Get context by ID
- `PUT /api/contexts/{context_id}` - Update context
- `DELETE /api/contexts/{context_id}` - Delete context
- `GET /api/contexts/search` - Search contexts

### Tools
- `POST /api/tools/register` - Register a new tool
- `POST /api/tools/{tool_id}/activate/{context_id}` - Activate tool for context
- `POST /api/tools/{tool_id}/deactivate/{context_id}` - Deactivate tool
- `GET /api/tools/active/{context_id}` - Get active tools for context
- `PATCH /api/tools/{tool_id}/status/{context_id}` - Update tool status

## Architecture

The system is built with a modular architecture:

- **Core**: Base functionality and configuration
- **Models**: Data models and schemas
- **Services**: Business logic and external integrations
- **API**: RESTful endpoints and routing
- **MCP**: Model Context Protocol implementation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
