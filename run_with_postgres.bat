@echo off
cd /d "%~dp0backend"
set DATABASE_URL=postgresql://truck_user:truck_password_123@localhost:5433/truck_movements
set TRUCK_API_BASE=http://127.0.0.1:8002
echo Starting Truck Monitoring API with PostgreSQL (Docker)...
echo API: http://127.0.0.1:8002
echo Docs: http://127.0.0.1:8002/docs
echo Health: http://127.0.0.1:8002/health
echo TRUCK_API_BASE set so axle background task can update axle_count.
echo.
uvicorn main:app --reload --host 127.0.0.1 --port 8002
