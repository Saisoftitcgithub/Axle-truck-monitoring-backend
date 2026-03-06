# Truck Monitoring Backend

FastAPI backend for a 3-stage truck monitoring flow: **Entry ANPR → Axle Detection → Exit ANPR**.  
Trip data is stored in `truck_movements` (active) and `truck_movements_completed` (exited); exit events are buffered in `exit_buffer` and matched by plate.

---

## Project structure

```
Axle Detection backend/
├── backend/                    # Application code (run uvicorn from here)
│   ├── main.py                 # FastAPI app, lifespan, router includes
│   ├── database.py             # SQLAlchemy engine, session, init_db
│   ├── models.py               # TruckMovement, TruckMovementCompleted, ExitBuffer
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── axle_runner.py          # Subprocess + internal API for axle detection
│   ├── scheduler_job.py        # Hourly: move EXITED to completed, process buffer
│   ├── routes/
│   │   ├── entry.py            # POST /entry-anpr
│   │   ├── axle.py             # POST /update-axle-status, POST /axle-detection
│   │   ├── exit.py             # POST /exit-anpr
│   │   └── db.py               # GET /db/tables, /db/tables/counts, /db/tables/data
│   ├── setup_postgres_simple.py # One-time Postgres DB setup (used by START_WITH_POSTGRES.bat)
│   └── truck_movements.db      # Created when using SQLite (gitignored)
├── requirements.txt            # Python dependencies
├── .env.example                # Copy to .env and set DATABASE_URL, AXLE_*, etc.
├── run.bat                     # Start server (Windows), port 8000
├── run.sh                      # Start server (Linux/macOS)
├── START_WITH_POSTGRES.bat     # Setup Postgres DB + start server on port 8002
├── docker-compose.yml          # PostgreSQL 15 (port 5433, truck_user)
└── README.md                   # This file
```

---

## Quick start

### 1. Install dependencies

From the **project root**:

```bash
pip install -r requirements.txt
```

### 2. (Optional) Environment

Copy `.env.example` to `.env` and set variables if needed. If you skip this, the app uses **SQLite** (`backend/truck_movements.db`) and default axle paths.

```bash
copy .env.example .env
# Edit .env: DATABASE_URL for PostgreSQL, or leave unset for SQLite
```

To load `.env` in the shell (e.g. for `uvicorn`), use a helper or set variables manually:

```bash
# Windows (PowerShell)
Get-Content .env | ForEach-Object { if ($_ -match '^([^#][^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process') } }

# Linux/macOS (with export in .env)
set -a && source .env && set +a
```

### 3. Run the server

**Option A — From project root (recommended):**

- **Windows:** double-click `run.bat` or run `run.bat` in a terminal  
- **Linux/macOS:** `./run.sh` or `bash run.sh`

**Option B — From backend directory:**

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- **API:** http://127.0.0.1:8000  
- **Docs:** http://127.0.0.1:8000/docs  
- **DB inspector:** http://127.0.0.1:8000/db/tables  

---

## Database

### SQLite (default)

If `DATABASE_URL` is not set, the app uses SQLite and creates `backend/truck_movements.db`. No extra setup.

### PostgreSQL

1. Create a database and user (e.g. in pgAdmin or psql):

   ```sql
   CREATE DATABASE truck_movements;
   CREATE USER your_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE truck_movements TO your_user;
   ```

2. Set the URL (in `.env` or in the shell):

   ```bash
   DATABASE_URL=postgresql://your_user:your_password@localhost:5432/truck_movements
   ```

3. Run the app; tables are created on startup.

### Docker Compose (PostgreSQL)

```bash
docker-compose up -d
```

Uses port **5433** (host) and credentials:

- User: `truck_user`  
- Password: `truck_password_123`  
- Database: `truck_movements`  

So:

```bash
DATABASE_URL=postgresql://truck_user:truck_password_123@localhost:5433/truck_movements
```

Then start the app (e.g. `run.bat` or `cd backend && uvicorn main:app --reload`).

### START_WITH_POSTGRES.bat (Windows)

Runs `backend/setup_postgres_simple.py` (creates DB if needed), sets `DATABASE_URL` for local PostgreSQL on port 5432, and starts the server on **port 8002**. You will be prompted for the `postgres` user password.

---

## Schema

Tables: **truck_movements** (active trips), **truck_movements_completed** (exited), **exit_buffer** (exit events before match). Full API and request/response schema: **http://127.0.0.1:8000/docs** when the server is running.

---

## Environment variables

| Variable             | Description                                                          |
|----------------------|----------------------------------------------------------------------|
| **DATABASE_URL**     | PostgreSQL URL. If unset, SQLite is used (backend/truck_movements.db). |
| **AXLE_MODEL_SCRIPT**| Path to process_video_tracking.py (axle detection script).          |
| **MODEL_PATH**       | Path to YOLO best.pt weights.                                        |
| **AXLE_VIDEO_PATH**   | Video file path for axle detection (script --video).                |
| **TRUCK_API_BASE**   | Base URL for axle_runner internal API (default http://127.0.0.1:8000). |

See `.env.example` for examples.

---

## API summary

| Method | Path                   | Description                                              |
|--------|------------------------|----------------------------------------------------------|
| POST   | `/entry-anpr`          | Create trip (IN_YARD), start axle detection; returns session_id. |
| POST   | `/exit-anpr`           | Buffer exit event, match by plate, set exit time/image (EXITED). |
| GET    | `/db/tables`           | List tables and columns.                                 |
| GET    | `/db/tables/counts`    | Row count per table.                                    |
| GET    | `/db/tables/data`      | Sample data from all tables.                            |

Internal (used by axle_runner, not in OpenAPI):

- POST `/update-axle-status` — set `axle_status` (e.g. PROCESSING, DONE, FAILED).  
- POST `/axle-detection` — submit `axle_count`, `processed_time`; set AXLE_DONE.

API docs and interactive schema: **http://127.0.0.1:8000/docs**

---

## Notes

- No Celery/Redis; axle detection runs in a FastAPI background task and calls the app over HTTP.
- Hourly job: moves EXITED rows from `truck_movements` to `truck_movements_completed` and processes unprocessed `exit_buffer` rows.
