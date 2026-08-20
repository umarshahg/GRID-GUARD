# GRID GUARD — Module 3: Graduated Response Engine

**Status:** ✅ Complete (5 Steps)

## Overview

Module 3 automatically responds to botnet threats detected by Module 2 using graduated response tiers based on risk scores.

## Architecture

```
Module 2 (Detection)
    ↓ Publishes risk scores via Redis
Module 3 Step 2 (Listener)
    ↓
Module 3 Step 1 (Decision Engine)
    ↓ Decides response tier
Module 3 Step 3 (Action Executor)
    ↓ Executes action (LOG, ALERT, RATE_LIMIT, ISOLATE)
Module 3 Step 4 (Database Logger)
    ↓ Saves to PostgreSQL
Module 3 Step 5 (Flask API)
    ↓ Exposes to Dashboard
Module 5 (Dashboard)
    Displays actions in real-time
```

## Files

| File | Purpose |
|------|---------|
| `module3_step1_response_engine.py` | Decision logic (Tier 1-4) |
| `module3_step2_listener.py` | Redis alert listener |
| `module3_step3_action_executor.py` | Execute actions |
| `module3_step4_database_logger.py` | Save to PostgreSQL |
| `module3_step5_flask_api.py` | REST API (Port 5002) |

## Installation

### On Linux (Ubuntu/Kali)

```bash
# Clone repository
git clone <your-repo>
cd module3_response_engine

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements_module3.txt

# Verify installation
python -c "import psycopg2; import flask_cors; print('✅ OK')"
```

### On Windows (with Docker)

```powershell
# Same as above but:
source .venv/Scripts/activate  # instead of source .venv/bin/activate
```

## Usage

### Test Individual Steps

```bash
# Step 1: Decision Logic
python module3_step1_response_engine.py

# Step 3: Action Executor
python module3_step3_action_executor.py

# Step 4: Database Logger
python module3_step4_database_logger.py
```

### Run Complete Pipeline

**Terminal 1: Module 2 Detection**
```bash
python detection_service.py
```

**Terminal 2: Module 3 Listener**
```bash
python module3_response_engine/module3_step2_listener.py
```

**Terminal 3: Module 3 API**
```bash
python module3_response_engine/module3_step5_flask_api.py
```

**Terminal 4: Dashboard**
```bash
cd webapp && python app.py
```

**Browser:**
```
http://localhost:5000
```

## Response Tiers

| Tier | Risk | Action | Description |
|------|------|--------|-------------|
| 1 | < 60% | LOG | Log only, no action |
| 2 | 60-80% | ALERT | Notify operator |
| 3 | 80-95% | RATE_LIMIT | Apply traffic limiting |
| 4 | >= 95% | FULL_ISOLATION | Sandbox isolation |

## API Endpoints

All endpoints on **Port 5002**

```bash
# Get recent actions
GET /api/actions/recent?limit=50

# Get actions for specific meter
GET /api/actions/meter/<meter_id>

# Get action counts
GET /api/actions/counts

# Get actions by tier
GET /api/actions/by-tier

# Health check
GET /api/health
```

## Database Schema

### audit_log table
```sql
log_id         INT (auto-increment)
actor          VARCHAR (Module3)
action_type    VARCHAR (LOG, ALERT, RATE_LIMIT, FULL_ISOLATION)
target_entity  VARCHAR (meter_id)
payload        JSONB (full decision data)
created_at     TIMESTAMP
```

## Configuration

Set environment variables:

```bash
# Database
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=gridguard
export DB_USER=gridguard
export DB_PASSWORD=gridguard

# Redis
export GRIDGUARD_REDIS_HOST=localhost
export GRIDGUARD_REDIS_PORT=6379

# Notifications (optional)
export GRID_GUARD_EMAIL_ENABLED=false
export GRID_GUARD_WEBHOOK_ENABLED=false
export GRID_GUARD_IPTABLES_ENABLED=false
```

## Dependencies

- **Python 3.11+**
- **PostgreSQL 15+** (via Docker)
- **Redis 7+** (via Docker)
- **Flask 3.0**
- **psycopg2-binary** (PostgreSQL driver)
- **redis** (Redis client)

## Testing

```bash
# Test database connection
python module3_step4_database_logger.py

# Test API
curl http://localhost:5002/api/health | jq

# Check recent actions
curl http://localhost:5002/api/actions/recent | jq
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'psycopg2'"
```bash
pip install psycopg2-binary flask-cors
```

### "Connection refused" (PostgreSQL)
```bash
# Start Docker containers
docker-compose up -d
sleep 10
```

### "Connection refused" (Redis)
```bash
# Redis is optional for Step 2
# Step 2 will work with or without it
```

## Performance

- Decision latency: < 1ms per flow
- Database write: < 10ms per action
- API response: < 50ms
- Database query: < 100ms

## SRS Compliance

| Requirement | Status |
|-------------|--------|
| FR-005: Graduated Response Engine | ✅ |
| FR-006: Detection Alert Generation | ✅ |
| Tier 1 (LOG) | ✅ |
| Tier 2 (ALERT) | ✅ |
| Tier 3 (RATE_LIMIT) | ✅ |
| Tier 4 (FULL_ISOLATION) | ✅ |
| Real-time API | ✅ |
| Database persistence | ✅ |

## Next Steps

- Module 4: Sandboxing & Isolation
- Module 5: Dashboard Integration
- Module 6: Full System Deployment

## Version

Module 3 v1.0.0 - Complete & Tested

## Author

GRID GUARD Team  
COMSATS University Islamabad
