# Wind Fault Orchestrator

A FastAPI backend service for managing wind turbine faults, alarms, and recommendations.

## Features

- 🚀 FastAPI for high-performance REST API
- 🗄️ SQLModel + SQLAlchemy for database operations
- 🐘 PostgreSQL support (with SQLite fallback for local development)
- ⚙️ Environment-based configuration
- 📊 Turbine registry and alarm ingestion
- 🤖 Rules engine for fault recommendations

## Project Structure

```
wind-fault-orchestrator/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── db.py                # Database configuration and session management
│   ├── models.py            # SQLModel database models
│   ├── schemas.py           # Pydantic schemas for API
│   ├── rules_engine.py      # Business logic for recommendations
│   └── routers/
│       ├── __init__.py
│       ├── turbines.py      # Turbine registry endpoints
│       ├── alarms.py        # Alarm ingestion endpoints
│       └── recommendations.py # Recommendation endpoints
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

## Setup

### 1. Clone and Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Access the API

- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc
- Health Check: http://localhost:8000/api/v1/health

## API Endpoints

### Turbines
- `POST /api/v1/turbines` - Register a new turbine
- `GET /api/v1/turbines` - List all turbines
- `GET /api/v1/turbines/{turbine_id}` - Get turbine details

### Alarms
- `POST /api/v1/alarms` - Ingest a new alarm
- `GET /api/v1/alarms` - List alarms with filters
- `GET /api/v1/alarms/{alarm_id}` - Get alarm details

### Recommendations
- `GET /api/v1/recommendations` - Get recommendations for alarms
- `GET /api/v1/recommendations/{alarm_id}` - Get recommendations for specific alarm

## Development

### Code Formatting

```bash
# Format with black
black app/

# Lint with ruff
ruff check app/
```

### Testing

```bash
pytest
```

## Database Migrations

For production use, consider adding Alembic for database migrations:

```bash
pip install alembic
alembic init migrations
```

## License

MIT License

