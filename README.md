# Truck Monitoring Backend

FastAPI backend for a 3-stage truck monitoring flow: **Entry ANPR → Axle Detection → Exit ANPR**.  
All truck data is stored in a single table (`truck_movements`), one row per trip.

## Project structure

```
backend/
├── main.py          # FastAPI app, lifespan, router includes
├── database.py      # SQLAlchemy engine, session, get_db, init_db
├── models.py        # TruckMovement ORM model
├── schemas.py       # Pydantic request/response schemas
├── axle_runner.py   # Subprocess + internal API calls for axle detection
├── routes/
│   ├── entry.py     # POST /entry-anpr
│   ├── axle.py      # POST /update-axle-status, POST /axle-detection
│   └── exit.py      # POST /exit-anpr
└── requirements.txt
```

## Run locally

From the **backend** directory:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

- API: http://127.0.0.1:8000  
- Docs: http://127.0.0.1:8000/docs  

## Database (PostgreSQL)

Create a database and set the connection URL:

```bash
# Example: create DB and user (run in psql or pgAdmin)
# CREATE DATABASE truck_movements;
# CREATE USER your_user WITH PASSWORD 'your_password';
# GRANT ALL PRIVILEGES ON DATABASE truck_movements TO your_user;
```

Set the environment variable (or the app uses the default below):

```bash
# Format: postgresql://USER:PASSWORD@HOST:PORT/DATABASE
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/truck_movements"
```

Default if unset: `postgresql://postgres:postgres@localhost:5432/truck_movements`.  
Tables are created automatically on startup.

## Environment (optional)

- **AXLE_MODEL_SCRIPT** – Path to `process_video_tracking.py` (default: your specified path).
- **MODEL_PATH** – Path to YOLO `best.pt` (default: your specified path).
- **AXLE_VIDEO_PATH** – Video file path for axle detection (script requires `--video`). Set for real runs.
- **TRUCK_API_BASE** – Base URL for internal API calls from axle_runner (default: `http://127.0.0.1:8000`).

## API summary

| Method | Path | Description |
|--------|------|-------------|
| POST | `/entry-anpr` | Create trip, set IN_YARD, start background axle detection |
| POST | `/update-axle-status` | Update `axle_status` (e.g. PROCESSING) |
| POST | `/axle-detection` | Set axle count, processed time, AXLE_DONE |
| POST | `/exit-anpr` | Match by plate, set exit time/image, EXITED |

No Celery/Redis; axle detection runs in a FastAPI background task and calls the same app over HTTP.
