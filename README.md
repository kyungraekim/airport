# Model Validation Bot

GitHub PR-based Model Validation Bot with FastAPI that automates model validation processes through PR comments using slash commands.

## Features

- **Slash Command Processing**: Parse and execute commands like `/train --epochs=10 --lr=0.001`
- **GitHub Integration**: Handle PR comments and post status updates
- **Async Job Management**: Execute long-running ML jobs with real-time progress
- **Mock Services**: Simulate JFrog and ML platform integrations for development
- **Real-time Updates**: WebSocket and Server-Sent Events for job progress
- **Model Validation**: Compare models and generate validation reports

## Supported Commands

```bash
/train --config=new --epochs=10 --lr=0.001 --gpu=2
/eval --model=baseline,incoming --metrics=accuracy,f1
/test --type=smoke --samples=100  
/pipeline --steps=train,eval --skip=test
/status --job=abc123
/help
```

## Quick Start

### Local Development

1. **Clone and setup:**
```bash
git clone <repository-url>
cd airport
cp .env.example .env  # Edit with your configuration
```

2. **Install dependencies (recommended: uv):**
```bash
# Using uv (recommended)
uv sync --dev

# Or using pip
pip install -e ".[dev]"
```

3. **Run the application:**
```bash
# Using uv
uv run serve
# or
uv run python -m app.main

# Using pip
python -m app.main
```

4. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Docker Development

1. **Using Docker Compose:**
```bash
docker-compose up --build
```

2. **Using Docker directly:**
```bash
docker build -t model-validation-bot .
docker run -p 8000:8000 --env-file .env model-validation-bot
```

## Usage Examples

### Manual Command Execution

```bash
curl -X POST "http://localhost:8000/commands/execute" \
  -H "Content-Type: application/json" \
  -d '{"command": "/train --epochs=5", "user_id": "developer"}'
```

### Quick Test Commands

```bash
# Test help command
curl -X POST "http://localhost:8000/commands/execute" \
  -H "Content-Type: application/json" \
  -d '{"command": "/help", "user_id": "test-user"}'

# Test training command  
curl -X POST "http://localhost:8000/commands/execute" \
  -H "Content-Type: application/json" \
  -d '{"command": "/train --epochs=3 --lr=0.001", "user_id": "test-user"}'

# Check active jobs
curl "http://localhost:8000/jobs/active"
```

### GitHub Webhook

Configure a GitHub webhook to point to `http://your-domain.com/webhook/github` with:
- Content type: `application/json`
- Secret: Your webhook secret
- Events: Issue comments

### Job Status Monitoring

```bash
# Get job status
curl "http://localhost:8000/jobs/{job_id}/status"

# Get all active jobs
curl "http://localhost:8000/jobs/active"

# Real-time updates via WebSocket
ws://localhost:8000/jobs/ws/{job_id}

# Server-Sent Events
curl "http://localhost:8000/jobs/{job_id}/stream"
```

## Project Structure

```
app/
├── api/                 # FastAPI routes
│   ├── webhooks.py     # GitHub webhook handling
│   ├── jobs.py         # Job status and management
│   └── commands.py     # Command execution
├── core/               # Configuration and settings
├── models/             # Pydantic data models
├── services/           # Business logic
│   ├── github_service.py      # GitHub API interactions
│   ├── command_processor.py   # Command parsing and execution
│   └── job_manager.py         # Job lifecycle management
├── mocks/              # Mock service implementations
│   ├── jfrog_service.py       # Mock JFrog Artifactory
│   └── workflow_service.py    # Mock ML platform
├── utils/              # Helper functions
└── main.py            # FastAPI application
tests/                  # Test files
```

## Configuration

The application uses environment variables. Copy `.env.example` to `.env` and configure:

### Required for GitHub Integration
```bash
GITHUB_WEBHOOK_SECRET=your-webhook-secret
GITHUB_TOKEN=your-github-token
```

### Mock Mode (Development)
```bash
MOCK_MODE=true  # Uses mock services
DEBUG=true      # Enable debug logging
```

### Production Mode
```bash
MOCK_MODE=false
JFROG_URL=https://your-jfrog-instance.com
JFROG_TOKEN=your-jfrog-token
ML_PLATFORM_URL=https://your-ml-platform.com
ML_PLATFORM_TOKEN=your-ml-platform-token
```

## Development

### Running Tests
```bash
# Using uv (recommended)
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_command_parser.py -v

# Using pip
pytest
pytest --cov=app
```

### Code Quality
```bash
# Using uv (recommended)
uv run black app/ tests/
uv run ruff check app/ tests/ --fix
uv run mypy app/

# All quality checks at once
uv run black app/ tests/ && uv run ruff check app/ tests/ && uv run mypy app/

# Using pip
black app/ tests/
ruff check app/ tests/ --fix
mypy app/
```

### Adding New Commands

1. **Add command type** to `app/models/commands.py`
2. **Update parser** in `app/utils/command_parser.py`
3. **Add execution logic** in `app/services/job_manager.py`
4. **Add tests** in `tests/`

### Adding Real Service Integration

1. **Create service class** in `app/services/`
2. **Update configuration** in `app/core/config.py`
3. **Modify mock flag** handling in job execution
4. **Add integration tests**

## API Documentation

### Endpoints

- `POST /webhook/github` - GitHub webhook receiver
- `POST /commands/execute` - Manual command execution
- `GET /jobs/{job_id}/status` - Get job status
- `GET /jobs/active` - List active jobs
- `POST /jobs/{job_id}/cancel` - Cancel job
- `WS /jobs/ws/{job_id}` - WebSocket job updates
- `GET /jobs/{job_id}/stream` - Server-sent events

### Command Format

Commands follow the format: `/{command} --param=value --flag`

**Parameters:**
- `--config=<name>` - Model configuration
- `--epochs=<n>` - Training epochs
- `--lr=<rate>` - Learning rate
- `--gpu=<count>` - GPU count
- `--model=<list>` - Model list (comma-separated)
- `--metrics=<list>` - Metrics list (comma-separated)

## GitHub Integration

### Setup Webhook

1. Go to repository Settings > Webhooks
2. Add webhook with URL: `https://your-domain.com/webhook/github`
3. Content type: `application/json`
4. Secret: Your webhook secret
5. Events: Issue comments

### PR Comment Workflow

1. User posts comment with slash command: `/train --epochs=5`
2. Bot validates command and creates job
3. Bot posts initial response with job ID
4. Job executes in background with progress updates
5. Bot updates comment with final results

## Deployment

### Docker Production

```bash
# Build production image
docker build -t model-validation-bot:latest .

# Run with production settings
docker run -d \
  --name model-validation-bot \
  -p 8000:8000 \
  --env-file .env.production \
  model-validation-bot:latest
```

### Environment Variables for Production

```bash
DEBUG=false
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@db:5432/model_validation
GITHUB_WEBHOOK_SECRET=your-webhook-secret
GITHUB_TOKEN=your-github-token
MOCK_MODE=false
```

## Troubleshooting

### uv Setup Issues

If `uv sync --dev` fails with build errors:

1. **Install uv** if not already installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clear cache and retry**:
```bash
uv cache clean
rm -rf .venv/
uv sync --dev
```

3. **Alternative: Use requirements file**:
```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements-dev.txt
uv pip install -e .
```

### Common Issues

- **Port conflicts**: Change port in `app/main.py` or kill existing process
- **Import errors**: Ensure installed with `uv sync --dev` or `pip install -e ".[dev]"`
- **Missing environment**: Copy `.env.example` to `.env`

### Debug Commands

```bash
# Test basic import
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
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run quality checks: `uv run black app/ && uv run ruff check app/ && uv run mypy app/ && uv run pytest`
5. Commit changes: `git commit -am 'Add feature'`
6. Push branch: `git push origin feature-name`
7. Create Pull Request

## License

MIT License - see LICENSE file for details.