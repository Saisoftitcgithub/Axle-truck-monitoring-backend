# Full test guide — Entry, Axle, Exit (with image and video)

Use these paths for testing:
- **Entry/Exit image:** `D:\Saisoft\Axle_Detection\New images 3\3.jpg`
- **Axle video:** `D:\Saisoft\Axle_Detection\Site truck video\Test2.mp4`

---

## Where images and video are “saved”

The backend **does not copy or save** image/video files. It only **stores the path string** you send in the database.

| What you send       | Where it’s stored in DB        | How to see the “output” |
|---------------------|--------------------------------|--------------------------|
| `image_path` (entry)| `truck_movements.entry_image`  | 1) View in API: GET `/db/tables/truck_movements/data` <br> 2) Open the path in Explorer or an image viewer |
| `image_path` (exit) | `exit_buffer.exit_image`, then `truck_movements.exit_image` | Same: check DB data, then open the path on disk |
| Video (axle)        | Not stored. Only `axle_count` and `axle_processed_time` are saved. | Set `AXLE_VIDEO_PATH`; the YOLO script uses that file. Any output (e.g. annotated video) is written by the script, not this API. |

So: **“Image output”** = the path stored in the DB. The actual file stays where you put it (e.g. `D:\Saisoft\Axle_Detection\New images 3\3.jpg`). Open that path to view the image.

---

## Prerequisites

1. **PostgreSQL running** (Docker):
   ```powershell
   cd "d:\Saisoft\Axle Detection backend"
   docker-compose up -d
   ```

2. **Start the API** with DB and (optional) video path for axle:
   ```powershell
   cd "d:\Saisoft\Axle Detection backend\backend"
   $env:DATABASE_URL = "postgresql://truck_user:truck_password_123@localhost:5433/truck_movements"
   $env:TRUCK_API_BASE = "http://127.0.0.1:8002"
   $env:AXLE_VIDEO_PATH = "D:\Saisoft\Axle_Detection\Site truck video\Test2.mp4"
   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8002
   ```
   Or use **run_with_postgres.bat** (it already sets `DATABASE_URL` and `TRUCK_API_BASE` for port 8002). Set `AXLE_VIDEO_PATH` in the same window before running if you want axle detection to use your video.

   **Why `axle_count` can be null:** The axle logic runs in a background task and calls the same API (e.g. POST /axle-detection) to save the count. If the server runs on a port other than 8000, you must set **TRUCK_API_BASE** to that URL (e.g. `http://127.0.0.1:8002`). Otherwise the background task gets 404 and never updates `axle_count`.

---

## Full test flow (manual)

### Step 1 — Health check

- Open: **http://127.0.0.1:8002/health**  
- Expect: `{"status":"ok","database":"connected"}`

### Step 2 — Entry ANPR (truck enters)

- **Swagger:** http://127.0.0.1:8002/docs → **POST /entry-anpr** → Try it out.  
- **Body (example):**
  ```json
  {
    "truck_id": "TRK-TEST-001",
    "plate_number": "TN01AB1234",
    "entry_time": "2026-02-03T10:15:22",
    "image_path": "D:\\Saisoft\\Axle_Detection\\New images 3\\3.jpg"
  }
  ```
- Click **Execute**.  
- Expect: **201** and a body with `session_id`, `status`: `IN_YARD`, `axle_status`: `PENDING`.  
- **What happens:** A row is added to `truck_movements` with `entry_image` = that path. A background task starts axle detection (if `AXLE_VIDEO_PATH` is set it uses your video).

### Step 3 — (Optional) Wait for axle detection

- If axle is running, after a while `axle_status` becomes `DONE` or `FAILED` and `axle_count` is set.  
- To see current state: **GET** http://127.0.0.1:8002/db/tables/truck_movements/data  
- Look at your `truck_id` row: `axle_status`, `axle_count`, `axle_processed_time`.

### Step 4 — Exit ANPR (truck leaves)

- **Swagger:** http://127.0.0.1:8002/docs → **POST /exit-anpr** → Try it out.  
- **Body (example):**
  ```json
  {
    "plate_number": "TN01AB1234",
    "exit_time": "2026-02-03T10:35:00",
    "image_path": "D:\\Saisoft\\Axle_Detection\\New images 3\\3.jpg"
  }
  ```
- Click **Execute**.  
- Expect: **200** and a body with `truck_id`, `session_id`, `status`: `EXITED`.  
- **What happens:** A row is added to `exit_buffer`, then it is matched to the truck by `plate_number`, and `truck_movements` is updated with `exit_time`, `exit_image`, `status` = EXITED.

### Step 5 — See “image output” and data

- **All table data:** http://127.0.0.1:8002/db/tables/data  
- **One table:** http://127.0.0.1:8002/db/tables/truck_movements/data  
- In the JSON you’ll see `entry_image` and `exit_image` (and paths for buffer). Copy a path and open it in Explorer or an image viewer to see the image.  
- **Video:** The file at `AXLE_VIDEO_PATH` is used by the YOLO script; the API does not save or serve the video. Any output (e.g. annotated video) is where the YOLO script writes it.

---

## Quick test (PowerShell)

Run from project root. Replace `TRK-XXX` with a new id if you run again.

```powershell
$base = "http://127.0.0.1:8002"
$entryImage = "D:\Saisoft\Axle_Detection\New images 3\3.jpg"
$exitImage  = "D:\Saisoft\Axle_Detection\New images 3\3.jpg"

# 1. Entry
Invoke-RestMethod -Uri "$base/entry-anpr" -Method Post -ContentType "application/json" -Body (@{
  truck_id = "TRK-TEST-001"
  plate_number = "TN01AB1234"
  entry_time = "2026-02-03T10:15:22"
  image_path = $entryImage
} | ConvertTo-Json)

# 2. Exit (same plate = matches the truck)
Invoke-RestMethod -Uri "$base/exit-anpr" -Method Post -ContentType "application/json" -Body (@{
  plate_number = "TN01AB1234"
  exit_time = "2026-02-03T10:35:00"
  image_path = $exitImage
} | ConvertTo-Json)

# 3. View data (entry_image and exit_image paths)
Invoke-RestMethod -Uri "$base/db/tables/truck_movements/data" -Method Get
```

---

## Using the axle video (Test2.mp4)

The backend does not store the video file. It passes the video path to the YOLO axle script via the environment variable **AXLE_VIDEO_PATH**.

1. **Set the variable when starting the server** (same window as uvicorn):
   ```powershell
   $env:AXLE_VIDEO_PATH = "D:\Saisoft\Axle_Detection\Site truck video\Test2.mp4"
   $env:TRUCK_API_BASE = "http://127.0.0.1:8002"
   cd "d:\Saisoft\Axle Detection backend\backend"
   $env:DATABASE_URL = "postgresql://truck_user:truck_password_123@localhost:5433/truck_movements"
   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8002
   ```
2. When you call **POST /entry-anpr**, a background task runs the axle script with that video. The script’s output (e.g. annotated video) is written wherever the YOLO script is configured to write it (not by this API).
3. The API only stores **axle_count** and **axle_processed_time** in `truck_movements` after the script finishes.

---

## Full test result (example run)

Using image `D:\Saisoft\Axle_Detection\New images 3\3.jpg` and (for axle) video `D:\Saisoft\Axle_Detection\Site truck video\Test2.mp4`:

| Step   | Result |
|--------|--------|
| Health | `{"status":"ok","database":"connected"}` |
| Entry  | 201 – `truck_id`: TRK-Demo-001, `session_id`: …, `status`: IN_YARD |
| Exit   | 200 – same truck, `status`: EXITED |
| Data   | `entry_image` and `exit_image` = `D:\Saisoft\Axle_Detection\New images 3\3.jpg` |

To see the image: open **D:\Saisoft\Axle_Detection\New images 3\3.jpg** in Explorer or an image viewer. The API only stores that path; it does not copy the file.

---

| Step   | Endpoint          | Image/Video path in body        | Where path is stored / used        |
|--------|-------------------|---------------------------------|------------------------------------|
| Entry  | POST /entry-anpr  | `image_path`: entry image path  | `truck_movements.entry_image`      |
| Axle   | (background)      | Set `AXLE_VIDEO_PATH` env       | Not stored; axle_count/time only   |
| Exit   | POST /exit-anpr   | `image_path`: exit image path   | `truck_movements.exit_image`       |
| View   | GET /db/tables/data or /db/tables/truck_movements/data | — | Copy `entry_image` / `exit_image` and open in Explorer/viewer. |
