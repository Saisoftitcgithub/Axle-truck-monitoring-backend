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
│   └── truck_movements.db      # Created when using SQLite (gitignored)
├── requirements.txt            # Python dependencies
├── run.bat                     # Start server (Windows), port 8000
├── run_with_postgres.bat       # Start server with Docker Postgres on port 8002
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

### 2. Run the server

**Option A — From project root (recommended):**

- **SQLite (no Postgres):** run `run.bat` (port 8000)
- **Docker Postgres:** run `run_with_postgres.bat` (port 8002)

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

## Full manual test (image + video)

The backend **does not save/copy** image/video files. It only stores the **path string** you send in the DB.

### 1. Start Docker Postgres

```powershell
cd "d:\Saisoft\Axle Detection backend"
docker-compose up -d
```

### 2. Start API (port 8002) with video for axle detection

```powershell
cd "d:\Saisoft\Axle Detection backend\backend"
$env:DATABASE_URL = "postgresql://truck_user:truck_password_123@localhost:5433/truck_movements"
$env:TRUCK_API_BASE = "http://127.0.0.1:8002"
$env:AXLE_VIDEO_PATH = "D:\Saisoft\Axle_Detection\Site truck video\Test2.mp4"
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8002
```

### 3. Entry (register truck)

Open `http://127.0.0.1:8002/docs` → **POST /entry-anpr** and send:

```json
{
  "truck_id": "TRK-TEST-001",
  "plate_number": "TN99DEMO001",
  "entry_time": "2026-02-03T10:15:22",
  "image_path": "D:\\Saisoft\\Axle_Detection\\New images 3\\3.jpg"
}
```

### 4. Wait for axle_count

Axle runs in the background. Check:
- `http://127.0.0.1:8002/db/tables/truck_movements/data`

Look for your `truck_id` and verify `axle_status` becomes `DONE` and `axle_count` is set.

### 5. Exit (register truck exit)

In docs, **POST /exit-anpr**:

```json
{
  "plate_number": "TN99DEMO001",
  "exit_time": "2026-02-03T10:35:00",
  "image_path": "D:\\Saisoft\\Axle_Detection\\New images 3\\3.jpg"
}
```

### 6. See the “image output”

In DB endpoints you will see `entry_image` and `exit_image` fields containing your paths. To view the image, open:
`D:\Saisoft\Axle_Detection\New images 3\3.jpg`

---

## Notes

- No Celery/Redis; axle detection runs in a FastAPI background task and calls the app over HTTP.
- Hourly job: moves EXITED rows from `truck_movements` to `truck_movements_completed` and processes unprocessed `exit_buffer` rows.
