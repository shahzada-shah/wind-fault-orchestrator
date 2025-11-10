# Wind Fault Orchestrator - Project Overview

## 🎯 Project Summary

A complete FastAPI backend service for wind turbine fault management, alarm ingestion, and automated recommendation generation.

## 📦 What's Included

### Core Application Files

```
app/
├── __init__.py          # Package initialization (107 bytes)
├── config.py            # Environment-based configuration (623 bytes)
├── db.py                # Database session management (833 bytes)
├── main.py              # FastAPI application & health check (2.3 KB)
├── models.py            # SQLModel database models (3.0 KB)
├── schemas.py           # Pydantic request/response schemas (4.2 KB)
├── rules_engine.py      # Business logic for recommendations (7.9 KB)
└── routers/
    ├── __init__.py      # Router package init
    ├── turbines.py      # Turbine CRUD endpoints (4.7 KB)
    ├── alarms.py        # Alarm ingestion & management (6.2 KB)
    └── recommendations.py # Recommendation endpoints (5.7 KB)
```

### Configuration Files

- **pyproject.toml** - Modern Python project configuration with all dependencies
- **requirements.txt** - Traditional pip requirements file
- **.env.example** - Environment variable template
- **.gitignore** - Git ignore patterns for Python projects

### Documentation

- **README.md** - Comprehensive project documentation
- **QUICKSTART.md** - Quick start guide with examples
- **PROJECT_OVERVIEW.md** - This file

### Utilities

- **run.sh** - Automated startup script (executable)
- **demo.py** - Interactive API demo script (8.2 KB)

## 🗄️ Database Models

### Turbine
- Unique turbine registry
- Track location, model, capacity
- Soft delete support (is_active flag)

### Alarm
- Alarm ingestion with severity levels
- Status tracking (active/acknowledged/resolved)
- Timestamps for alarm lifecycle
- Linked to turbine

### Recommendation
- Auto-generated or manual recommendations
- Priority levels (low/medium/high/urgent)
- Action items and estimated downtime
- Linked to alarm

## 🔌 API Endpoints

### Turbines (`/api/v1/turbines`)
- `POST /` - Register new turbine
- `GET /` - List turbines (with filters)
- `GET /{turbine_id}` - Get turbine details
- `PATCH /{turbine_id}` - Update turbine
- `DELETE /{turbine_id}` - Soft delete turbine

### Alarms (`/api/v1/alarms`)
- `POST /` - Ingest new alarm (auto-generates recommendation)
- `GET /` - List alarms (with filters)
- `GET /{alarm_id}` - Get alarm details
- `PATCH /{alarm_id}` - Update alarm status
- `POST /{alarm_id}/acknowledge` - Acknowledge alarm
- `POST /{alarm_id}/resolve` - Resolve alarm

### Recommendations (`/api/v1/recommendations`)
- `GET /` - List all recommendations (sorted by priority)
- `GET /{alarm_id}` - Get recommendations for specific alarm
- `POST /{alarm_id}/generate` - Generate new recommendation
- `POST /` - Create manual recommendation
- `GET /recommendation/{id}` - Get specific recommendation

### Health Check
- `GET /api/v1/health` - API and database health status

## 🤖 Rules Engine

Built-in alarm codes with automated recommendations:

| Alarm Code | Priority | Est. Downtime |
|------------|----------|---------------|
| GEARBOX_TEMP_HIGH | Urgent | 4 hours |
| GENERATOR_VIBRATION | High | 8 hours |
| PITCH_SYSTEM_FAULT | High | 12 hours |
| YAW_ERROR | Medium | 6 hours |
| GRID_DISCONNECT | Urgent | 2 hours |
| LOW_WIND_SPEED | Low | 0 hours |

**Fallback:** For unknown alarm codes, generates recommendations based on severity level.

## 🚀 Quick Start

### Easiest Way
```bash
cd wind-fault-orchestrator
./run.sh
```

### Manual Way
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

### Try the Demo
```bash
# Terminal 1: Start server
uvicorn app.main:app --reload

# Terminal 2: Run demo
python demo.py
```

## 🔧 Technology Stack

- **FastAPI** - Modern, fast web framework
- **SQLModel** - SQL databases with Python type hints
- **SQLAlchemy** - Powerful ORM
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server
- **PostgreSQL/SQLite** - Database (configurable)

## 📊 Features

✅ Full CRUD operations for turbines  
✅ Alarm ingestion with automatic recommendation generation  
✅ Rules-based recommendation engine  
✅ Severity and priority-based filtering  
✅ Alarm lifecycle management (active → acknowledged → resolved)  
✅ SQLite for local dev, PostgreSQL for production  
✅ Environment-based configuration  
✅ Auto-generated API documentation (OpenAPI/Swagger)  
✅ Type-safe with Pydantic models  
✅ Database session management  
✅ CORS support  
✅ Health check endpoint  

## 🎓 Code Quality

- Black formatting ready
- Ruff linting ready
- Type hints throughout
- Clear separation of concerns
- RESTful API design
- Dependency injection pattern

## 📝 Example Usage

```python
import httpx

# Register a turbine
response = httpx.post("http://localhost:8000/api/v1/turbines", json={
    "turbine_id": "WT-001",
    "name": "Wind Turbine 1",
    "location": "North Field",
    "model": "Vestas V90",
    "capacity_kw": 2000
})

# Ingest an alarm (auto-generates recommendation)
response = httpx.post("http://localhost:8000/api/v1/alarms", json={
    "turbine_id": "WT-001",
    "alarm_code": "GEARBOX_TEMP_HIGH",
    "alarm_description": "Temperature exceeds 85°C",
    "severity": "high"
})

# Get recommendations
response = httpx.get("http://localhost:8000/api/v1/recommendations")
recommendations = response.json()
```

## 🔮 Future Enhancements

- [ ] JWT authentication
- [ ] Rate limiting
- [ ] WebSocket support for real-time alarms
- [ ] Celery for background tasks
- [ ] Alembic database migrations
- [ ] Unit and integration tests
- [ ] ML-based predictive recommendations
- [ ] Time-series data storage
- [ ] Alarm aggregation and trending
- [ ] Email/SMS notifications
- [ ] Grafana dashboards
- [ ] Docker containerization
- [ ] CI/CD pipeline

## 📄 License

MIT License

## 🙏 Acknowledgments

Built with modern Python best practices for wind turbine fault management and orchestration.

---

**Ready to use!** Start with `./run.sh` and visit http://localhost:8000/docs

