# CLAUDE.md - Development Context

This repository contains multiple components. The Model Validation Bot server is located in the `bot-server/` directory.

## Project Overview

A GitHub PR-based Model Validation Bot built with FastAPI that automates model validation processes through PR comments using slash commands. The bot handles model delivery from external teams, compares against reference models, and triggers ML training/evaluation workflows.

## Key Commands for Development

### Setup and Dependencies
```bash
# Navigate to bot-server directory
cd bot-server

# Install with uv (recommended)
uv sync --dev

# Or with pip
pip install -e ".[dev]"

# Run application
uv run serve
# or
uv run python -m app.main
```

### Testing
```bash
# Navigate to bot-server directory first
cd bot-server

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test categories
uv run pytest tests/test_command_parser.py -v
uv run pytest tests/test_api.py -v
uv run pytest tests/test_mocks.py -v

# Test API endpoints manually
curl -X POST "http://localhost:8000/commands/execute" \
  -H "Content-Type: application/json" \
  -d '{"command": "/help", "user_id": "developer"}'
```

### Code Quality
```bash
# Navigate to bot-server directory first
cd bot-server

# Format code
uv run black app/ tests/

# Lint code  
uv run ruff check app/ tests/ --fix

# Type checking
uv run mypy app/

# Run all quality checks
uv run black app/ tests/ && uv run ruff check app/ tests/ && uv run mypy app/ && uv run pytest
```

## Architecture Overview

### Core Components
- **FastAPI Application** (`bot-server/app/main.py`) - Main REST API with async support
- **Slash Command System** (`bot-server/app/utils/command_parser.py`) - Parse commands like `/train --epochs=10`
- **Job Management** (`bot-server/app/services/job_manager.py`) - Async background task execution
- **GitHub Integration** (`bot-server/app/services/github_service.py`) - PR comment handling and updates
- **Mock Services** (`bot-server/app/mocks/`) - Development-ready JFrog and ML platform simulators

### Supported Slash Commands
```bash
/train --config=new --epochs=10 --lr=0.001 --gpu=2
/eval --model=baseline,incoming --metrics=accuracy,f1
/test --type=smoke --samples=100
/pipeline --steps=train,eval --skip=test  
/status --job=abc123
/help
```

### API Endpoints
- `POST /webhook/github` - GitHub webhook receiver
- `POST /commands/execute` - Manual command execution
- `GET /jobs/{job_id}/status` - Job status queries
- `GET /jobs/active` - List active jobs
- `WS /jobs/ws/{job_id}` - WebSocket real-time updates
- `GET /jobs/{job_id}/stream` - Server-sent events

## Development Workflow

### Adding New Commands
1. Add command type to `bot-server/app/models/commands.py`
2. Update parser in `bot-server/app/utils/command_parser.py`
3. Add execution logic in `bot-server/app/services/job_manager.py`
4. Add tests in `bot-server/tests/`

### Mock vs Real Services
- Set `MOCK_MODE=true` in `.env` for development with mock services
- Set `MOCK_MODE=false` for production with real JFrog/ML platform integration
- Mock services provide realistic delays, progress updates, and responses

### Testing GitHub Webhooks Locally
1. Use ngrok: `ngrok http 8000`
2. Set GitHub webhook URL to: `https://xxx.ngrok.io/webhook/github`
3. Test with mock payload:
```bash
curl -X POST "http://localhost:8000/webhook/github" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issue_comment" \
  -d '{"action": "created", "comment": {"body": "/train --epochs=3", ...}}'
```

## Project Structure
```
bot-server/             # Model Validation Bot server
├── app/
│   ├── api/           # FastAPI routes
│   ├── core/          # Configuration and settings  
│   ├── models/        # Pydantic data models
│   ├── services/      # Business logic
│   ├── mocks/         # Mock service implementations
│   ├── utils/         # Helper functions
│   └── main.py        # Application entry point
├── tests/             # Test files
├── pyproject.toml     # Python project configuration
├── Dockerfile         # Container configuration
└── docker-compose.yml # Development environment
```

## Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:

**Development (Mock Mode):**
```bash
DEBUG=true
MOCK_MODE=true
GITHUB_WEBHOOK_SECRET=your-webhook-secret
GITHUB_TOKEN=your-github-token
```

**Production:**
```bash
DEBUG=false
MOCK_MODE=false
JFROG_URL=https://your-jfrog-instance.com
ML_PLATFORM_URL=https://your-ml-platform.com
DATABASE_URL=postgresql://user:pass@db:5432/model_validation
```

## Debugging Tips

### Common Issues
- **Port conflicts**: Change port in `app/main.py` or kill existing process
- **Import errors**: Ensure installed with `uv sync --dev` or `pip install -e .`
- **Build failures**: Check `pyproject.toml` configuration and hatchling setup

### Useful Debug Commands
```bash
# Navigate to bot-server directory first
cd bot-server

# Check if imports work
uv run python -c "import app.main; print('✅ Import successful!')"

# Test mock services
uv run python -c "
import asyncio
from app.mocks.jfrog_service import MockJFrogService
async def test(): 
    service = MockJFrogService()
    artifacts = await service.list_artifacts('ml-models-local')
    print(f'Found {len(artifacts)} artifacts')
asyncio.run(test())
"

# Monitor job execution
curl http://localhost:8000/jobs/active
curl http://localhost:8000/jobs/{job_id}/status
```

## Docker Usage

### Development
```bash
# Navigate to bot-server directory
cd bot-server

# Build and run with docker-compose
docker-compose up --build
```

### Production
```bash
# Navigate to bot-server directory
cd bot-server

# Build and run production container
docker build -t model-validation-bot .
docker run -p 8000:8000 --env-file .env.production model-validation-bot
```

## Next Steps for Production

1. **Replace Mock Services**: Implement real JFrog and ML platform integrations
2. **Database**: Switch from SQLite to PostgreSQL for job persistence  
3. **Authentication**: Add proper GitHub App authentication
4. **Monitoring**: Add logging, metrics, and health checks
5. **Rate Limiting**: Implement request rate limiting and job queue management

This project provides a solid foundation that can be easily adapted for internal use by replacing mock services with real integrations.