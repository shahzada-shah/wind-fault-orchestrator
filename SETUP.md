# Wind Fault Orchestrator - Quick Setup Guide

## 🚀 Quick Start (3 Methods)

### Method 1: Docker Compose (Easiest - Production Ready)

```bash
# Clone and navigate to directory
cd wind-fault-orchestrator

# Start all services (PostgreSQL + API + Adminer)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

**Access Points:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database Admin (Adminer): http://localhost:8080
  - System: PostgreSQL
  - Server: postgres
  - Username: wfo_user
  - Password: wfo_password
  - Database: wind_fault_orchestrator

### Method 2: Local Development with SQLite

```bash
# Install Python 3.10+
python --version  # Should be 3.10 or higher

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Create .env file
cp .env.example .env

# Run the application
uvicorn app.main:app --reload

# Or use the startup script
chmod +x run.sh
./run.sh
```

### Method 3: Using the Startup Script

```bash
chmod +x run.sh
./run.sh
```

This script automatically:
- Creates virtual environment
- Installs dependencies
- Creates .env file
- Starts the server

---

## 🧪 Testing the API

### Option 1: Interactive Docs (Easiest)
1. Open http://localhost:8000/docs
2. Click on any endpoint
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"

### Option 2: REST Client (VS Code)
1. Install "REST Client" extension in VS Code
2. Open `requests.http`
3. Click "Send Request" above any request block

### Option 3: curl Commands

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Register a turbine
curl -X POST http://localhost:8000/api/v1/turbines \
  -H "Content-Type: application/json" \
  -d '{
    "turbine_id": "WT-001",
    "name": "Wind Turbine 1",
    "location": "North Field",
    "model": "Vestas V90",
    "capacity_kw": 2000
  }'

# Ingest an alarm (auto-generates recommendation)
curl -X POST http://localhost:8000/api/v1/alarms \
  -H "Content-Type: application/json" \
  -d '{
    "turbine_id": "WT-001",
    "alarm_code": "EM_83",
    "alarm_description": "Critical fault",
    "severity": "critical",
    "resettable": true,
    "temperature_c": 82.5
  }'

# Get analytics summary
curl http://localhost:8000/api/v1/analytics/summary

# Get top faults
curl http://localhost:8000/api/v1/analytics/top-faults?limit=5
```

---

## 🎮 Demo Workflow

### 1. Register Turbines
```bash
# Register 3 turbines
curl -X POST http://localhost:8000/api/v1/turbines \
  -H "Content-Type: application/json" \
  -d '{"turbine_id": "FR-101", "name": "France Turbine 101", "location": "Normandy", "model": "Vestas V90", "capacity_kw": 2000}'

curl -X POST http://localhost:8000/api/v1/turbines \
  -H "Content-Type: application/json" \
  -d '{"turbine_id": "FR-102", "name": "France Turbine 102", "location": "Normandy", "model": "Vestas V90", "capacity_kw": 2000}'

curl -X POST http://localhost:8000/api/v1/turbines \
  -H "Content-Type: application/json" \
  -d '{"turbine_id": "DE-201", "name": "Germany Turbine 201", "location": "North Sea", "model": "Siemens SWT-3.6", "capacity_kw": 3600}'
```

### 2. Test Oscillation Detection
```bash
# Send same alarm twice within 10 minutes
curl -X POST http://localhost:8000/api/v1/alarms \
  -H "Content-Type: application/json" \
  -d '{"turbine_id": "FR-101", "alarm_code": "EM_83", "alarm_description": "Test 1", "severity": "major", "resettable": true, "temperature_c": 70}'

# Wait a few seconds, then send again
sleep 5

curl -X POST http://localhost:8000/api/v1/alarms \
  -H "Content-Type: application/json" \
  -d '{"turbine_id": "FR-101", "alarm_code": "EM_83", "alarm_description": "Test 2", "severity": "major", "resettable": true, "temperature_c": 71}'

# Check recommendation - should be ESCALATE due to oscillation
curl http://localhost:8000/api/v1/recommendations
```

### 3. Test Temperature Logic
```bash
# High temperature alarm (>75°C) for critical code
curl -X POST http://localhost:8000/api/v1/alarms \
  -H "Content-Type: application/json" \
  -d '{"turbine_id": "FR-102", "alarm_code": "GEARBOX_TEMP_HIGH", "alarm_description": "Gearbox overheating", "severity": "high", "resettable": true, "temperature_c": 82.5}'

# Check recommendation - should be WAIT_COOL_DOWN
# Check turbine state - should be "Cooling"
curl http://localhost:8000/api/v1/turbines
```

### 4. View Analytics
```bash
# Summary
curl http://localhost:8000/api/v1/analytics/summary

# Top faults
curl http://localhost:8000/api/v1/analytics/top-faults?limit=10

# Troubled turbines
curl http://localhost:8000/api/v1/analytics/turbines/troubled?limit=5

# Temperature trends
curl "http://localhost:8000/api/v1/analytics/temp-trends/1?days=7"
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --reload --port 8080
```

### Database Connection Issues (Docker)
```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres

# Restart services
docker-compose restart
```

### Virtual Environment Issues
```bash
# Remove and recreate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Module Not Found Errors
```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # Should see (venv) in prompt

# Reinstall dependencies
pip install -e ".[dev]"
```

---

## 📊 Monitoring

### View Application Logs
```bash
# Docker
docker-compose logs -f app

# Local
# Logs print to console by default
```

### Check Background Worker
The background worker checks snoozed alarms every 60 seconds.

Look for log messages like:
```
INFO:app.background_worker:Background worker started
INFO:app.background_worker:Found 2 expired snoozed alarms
INFO:app.background_worker:Re-evaluating snoozed alarm 5
```

### Database Inspection
```bash
# Using Adminer (Docker)
# Open http://localhost:8080

# Using psql (Docker)
docker exec -it wfo-postgres psql -U wfo_user -d wind_fault_orchestrator

# Using SQLite browser (Local)
sqlite3 wind_turbines.db
.tables
.schema alarms
SELECT * FROM alarms;
```

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Database
DATABASE_URL=sqlite:///./wind_turbines.db
# or for PostgreSQL:
# DATABASE_URL=postgresql://wfo_user:wfo_password@localhost:5432/wind_fault_orchestrator

# Application
ENV=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
PROJECT_NAME=Wind Fault Orchestrator
VERSION=1.0.0
API_V1_PREFIX=/api/v1
```

### Rules Engine Tuning (app/rules_engine.py)
```python
TEMP_THRESHOLD = 75.0  # Temperature threshold for cool-down
FREQ_24H_THRESHOLD = 4  # Alarms in 24h before escalation
FREQ_7D_THRESHOLD = 8   # Alarms in 7d before escalation
OSCILLATION_WINDOW = 10 # Minutes for oscillation detection
DEFAULT_SNOOZE_MINUTES = 20  # Default snooze duration
```

### Background Worker Tuning (app/background_worker.py)
```python
worker = BackgroundWorker(check_interval=60)  # Check every 60 seconds
```

---

## 📚 Documentation

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Project Overview**: `PROJECT_OVERVIEW.md`
- **Quickstart Guide**: `QUICKSTART.md`
- **Enhancements**: `ENHANCEMENTS.md`
- **This Setup Guide**: `SETUP.md`

---

## 🎯 Next Steps

1. ✅ Register turbines
2. ✅ Ingest alarms
3. ✅ View auto-generated recommendations
4. ✅ Check analytics
5. ✅ Monitor troubled turbines
6. ✅ Track temperature trends

---

## 💡 Tips

- Use the interactive docs at `/docs` for the easiest testing experience
- The `requests.http` file has 40+ ready-to-use test cases
- Background worker logs help debug snooze behavior
- Analytics endpoints support time filtering (1-365 days)
- All alarms auto-generate recommendations with the advanced rules engine

---

## 🆘 Need Help?

1. Check the logs: `docker-compose logs -f app`
2. Verify database: http://localhost:8080 (Adminer)
3. Test API health: `curl http://localhost:8000/api/v1/health`
4. Review documentation at http://localhost:8000/docs

---

**Happy Orchestrating! 🌬️💨**

