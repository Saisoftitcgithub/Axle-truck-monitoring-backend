#!/usr/bin/env bash
cd "$(dirname "$0")/backend"
echo "Starting Truck Monitoring API (SQLite if DATABASE_URL not set)..."
echo "API: http://127.0.0.1:8000"
echo "Docs: http://127.0.0.1:8000/docs"
echo ""
exec uvicorn main:app --reload --host 127.0.0.1 --port 8000
