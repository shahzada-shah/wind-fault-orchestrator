# Quick Start Guide

## Installation & Setup

### Option 1: Using the run script (Recommended)

```bash
cd wind-fault-orchestrator
./run.sh
```

This script will:
- Create a virtual environment
- Install all dependencies
- Copy `.env.example` to `.env`
- Start the server with auto-reload

### Option 2: Manual setup

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Configure environment
cp .env.example .env

# 4. Run the server
uvicorn app.main:app --reload
```

## Using the API

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

## Example API Workflow

### 1. Register a Turbine

```bash
curl -X POST "http://localhost:8000/api/v1/turbines" \
  -H "Content-Type: application/json" \
  -d '{
    "turbine_id": "WT-001",
    "name": "Wind Turbine 1",
    "location": "North Field",
    "model": "Vestas V90",
    "capacity_kw": 2000,
    "installation_date": "2020-01-15T00:00:00",
    "is_active": true
  }'
```

### 2. Ingest an Alarm

```bash
curl -X POST "http://localhost:8000/api/v1/alarms" \
  -H "Content-Type: application/json" \
  -d '{
    "turbine_id": "WT-001",
    "alarm_code": "GEARBOX_TEMP_HIGH",
    "alarm_description": "Gearbox temperature exceeds 85°C",
    "severity": "high",
    "occurred_at": "2024-01-20T10:30:00"
  }'
```

This will automatically generate a recommendation based on the rules engine.

### 3. Get Recommendations

```bash
# Get all recommendations
curl "http://localhost:8000/api/v1/recommendations"

# Get recommendations for specific alarm (replace {alarm_id})
curl "http://localhost:8000/api/v1/recommendations/{alarm_id}"
```

### 4. List Turbines

```bash
# Get all turbines
curl "http://localhost:8000/api/v1/turbines"

# Get active turbines only
curl "http://localhost:8000/api/v1/turbines?is_active=true"
```

### 5. List Alarms

```bash
# Get all alarms
curl "http://localhost:8000/api/v1/alarms"

# Get active alarms
curl "http://localhost:8000/api/v1/alarms?status=active"

# Get alarms for specific turbine
curl "http://localhost:8000/api/v1/alarms?turbine_id=WT-001"
```

### 6. Acknowledge or Resolve an Alarm

```bash
# Acknowledge alarm
curl -X POST "http://localhost:8000/api/v1/alarms/{alarm_id}/acknowledge"

# Resolve alarm
curl -X POST "http://localhost:8000/api/v1/alarms/{alarm_id}/resolve"
```

## Database Configuration

### SQLite (Default - Local Development)

The default configuration uses SQLite, which requires no additional setup:

```env
DATABASE_URL=sqlite:///./wind_turbines.db
```

### PostgreSQL (Production)

For production, update `.env`:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/wind_fault_orchestrator
```

Make sure PostgreSQL is installed and running:

```bash
# macOS
brew install postgresql
brew services start postgresql

# Create database
createdb wind_fault_orchestrator
```

## Alarm Codes & Rules Engine

The system includes built-in rules for common alarm codes:

| Alarm Code | Priority | Action |
|------------|----------|--------|
| `GEARBOX_TEMP_HIGH` | Urgent | Immediate inspection, reduce load |
| `GENERATOR_VIBRATION` | High | Vibration analysis, bearing inspection |
| `PITCH_SYSTEM_FAULT` | High | Stop turbine, inspect pitch motors |
| `YAW_ERROR` | Medium | Inspect yaw motors and sensors |
| `GRID_DISCONNECT` | Urgent | Check grid connection, verify relays |
| `LOW_WIND_SPEED` | Low | Monitor conditions, check sensors |

For unknown alarm codes, the system generates recommendations based on severity levels.

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Code Quality

```bash
# Format code with black
black app/

# Lint with ruff
ruff check app/

# Auto-fix linting issues
ruff check --fix app/
```

## Project Structure

```
wind-fault-orchestrator/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # FastAPI app & routes
│   ├── config.py             # Configuration management
│   ├── db.py                 # Database setup
│   ├── models.py             # SQLModel database models
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── rules_engine.py       # Business logic for recommendations
│   └── routers/              # API route modules
│       ├── __init__.py
│       ├── turbines.py       # Turbine management endpoints
│       ├── alarms.py         # Alarm ingestion endpoints
│       └── recommendations.py # Recommendation endpoints
├── pyproject.toml            # Project metadata & dependencies
├── requirements.txt          # Alternative dependency list
├── .env.example              # Environment variable template
├── .gitignore               # Git ignore rules
├── run.sh                   # Quick start script
├── README.md                # Full documentation
└── QUICKSTART.md            # This file
```

## Next Steps

1. **Add Authentication**: Implement JWT or API key authentication
2. **Add Tests**: Create unit and integration tests
3. **Add Logging**: Implement structured logging
4. **Add Migrations**: Use Alembic for database migrations
5. **Add Monitoring**: Integrate with Prometheus/Grafana
6. **Expand Rules Engine**: Add more sophisticated ML-based rules
7. **Add WebSocket**: Real-time alarm notifications
8. **Add Background Tasks**: Use Celery for async processing

## Troubleshooting

### Port Already in Use

```bash
# Change port in .env
PORT=8001

# Or specify when running
uvicorn app.main:app --port 8001
```

### Database Connection Issues

```bash
# Check database file permissions (SQLite)
ls -l wind_turbines.db

# Test PostgreSQL connection
psql -U username -d wind_fault_orchestrator
```

### Import Errors

```bash
# Reinstall dependencies
pip install -e ".[dev]" --force-reinstall
```

## Support

For issues, questions, or contributions, please refer to the main README.md.

