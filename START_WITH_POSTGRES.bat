@echo off
echo ========================================
echo Truck Monitoring - PostgreSQL Setup
echo ========================================
echo.
echo PostgreSQL is already running on port 5432.
echo.
set /p PGPASS="Enter PostgreSQL 'postgres' user password: "
echo.
echo Setting up database...
cd backend
python setup_postgres_simple.py
echo.
echo ========================================
echo Starting FastAPI Server with PostgreSQL
echo ========================================
echo.
set DATABASE_URL=postgresql://postgres:%PGPASS%@localhost:5432/truck_movements
echo DATABASE_URL is set
echo.
echo Server will start on: http://127.0.0.1:8002
echo API Docs: http://127.0.0.1:8002/docs
echo View Tables: http://127.0.0.1:8002/db/tables
echo.
pause
uvicorn main:app --host 127.0.0.1 --port 8002
