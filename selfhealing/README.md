# AI-Powered Bug Detection & Self-Healing System

An intelligent system that combines Grafana monitoring with AI-powered bug detection and automated self-healing capabilities.

## Features

- **AI-Powered Analysis**: Uses Claude 3.5 Sonnet via OpenRouter for intelligent log analysis
- **Automatic Bug Detection**: Detects bugs from logs and Grafana alerts with confidence scoring
- **Self-Healing**: Automatically attempts to heal detected bugs based on risk level
- **GitHub Integration**: Creates issues for bugs that require manual intervention
- **Health Monitoring**: Tracks service health scores and metrics
- **Dashboard Statistics**: Provides real-time insights into system health
- **API Authentication**: Optional API key authentication for secure access

## Architecture

```
app/
├── core/           # Core functionality (config, database, auth)
├── models/         # Pydantic models
├── services/       # Business logic services
├── api/            # FastAPI routers
└── main.py         # Application entry point
```

## Installation

1. **Clone the repository**
```bash
cd /Users/supunchathuranga/Documents/hackathon27/AIBugHunter
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start MongoDB**
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or use your existing MongoDB instance
```

## Configuration

Edit `.env` file with your settings:

- `MONGODB_URI`: MongoDB connection string
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `OPENROUTER_BASE_URL`: OpenRouter API base URL
- `PORT`: Application port (default: 8000)
- `ENV`: Environment (development, staging, production)
- `GITHUB_TOKEN`: (Optional) GitHub personal access token
- `GITHUB_REPO`: (Optional) GitHub repository for issues

## Running the Application

```bash
# Development mode
python app/main.py

# Or using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

Once running, access the interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Log Analysis
- `POST /api/v1/logs/ingest` - Ingest and analyze logs

### Grafana Integration
- `POST /api/v1/grafana/webhook` - Receive Grafana alerts

### Bug Management
- `GET /api/v1/bugs` - List detected bugs
- `GET /api/v1/bugs/{bug_id}` - Get bug details
- `POST /api/v1/bugs/{bug_id}/heal` - Trigger self-healing

### Monitoring
- `GET /api/v1/dashboard/stats` - Dashboard statistics
- `GET /api/v1/health/{service_name}` - Service health score

## Authentication

The API supports optional authentication via:

1. **Bearer Token**
```bash
curl -H "Authorization: Bearer your_api_key" http://localhost:8000/api/v1/bugs
```

2. **X-API-Key Header**
```bash
curl -H "X-API-Key: your_api_key" http://localhost:8000/api/v1/bugs
```

3. **Query Parameter**
```bash
curl http://localhost:8000/api/v1/bugs?api_key=your_api_key
```

## Grafana Integration

Configure Grafana to send webhooks to your application:

1. In Grafana, go to Alerting > Contact Points
2. Add a new contact point with type "Webhook"
3. Set URL to: `http://your-server:8000/api/v1/grafana/webhook`
4. Add custom header `X-API-Key: your_api_key` (if using authentication)

## Example Usage

### Ingest Logs for Analysis

```bash
curl -X POST http://localhost:8000/api/v1/logs/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "logs": [
      {
        "timestamp": "2025-01-15T10:30:00Z",
        "level": "ERROR",
        "service": "api-gateway",
        "message": "Database connection pool exhausted"
      }
    ],
    "service_name": "api-gateway",
    "time_range": "Last 5 minutes"
  }'
```

### Trigger Self-Healing

```bash
curl -X POST http://localhost:8000/api/v1/bugs/bug_abc123/heal
```

## Self-Healing Configuration

The system supports risk-based automation:

- **Low Risk**: Auto-approved (cache clearing, retries)
- **Medium Risk**: Auto-approved by default (service restarts, configuration reloads)
- **High Risk**: Requires manual approval (rollbacks, security changes)

Configure in `.env`:
```env
AUTO_HEAL_LOW_RISK=true
AUTO_HEAL_MEDIUM_RISK=true
AUTO_HEAL_HIGH_RISK=false
```

## Development

### Project Structure

- `app/core/config.py` - Application configuration
- `app/core/database.py` - MongoDB connection management
- `app/core/auth.py` - API key authentication
- `app/models/` - Pydantic models for data validation
- `app/services/bug_detection_service.py` - AI-powered bug detection
- `app/services/self_healing_service.py` - Automated healing logic
- `app/services/github_service.py` - GitHub integration
- `app/api/monitoring.py` - API endpoints

### Adding New Healing Actions

Edit `app/services/self_healing_service.py` and add actions to `_initialize_healing_actions()`:

```python
BugCategory.YOUR_CATEGORY: [
    HealingAction(
        action_type="your_action",
        description="Description",
        risk_level=RiskLevel.LOW
    ),
]
```

## License

MIT License

## Support

For issues and questions, please create an issue on GitHub.
