from contextlib import asynccontextmanager
import traceback

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from sqlalchemy import text
from sqlalchemy.orm import Session

from database import init_db, get_db
from routes import entry, axle, exit as exit_router, db as db_router
from scheduler_job import run_hourly_job

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.add_job(run_hourly_job, "interval", hours=1, id="hourly_move_and_buffer")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Truck Monitoring API",
    description="Entry ANPR → Axle Detection → Exit ANPR",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return 500 with error detail so we can see what went wrong."""
    tb = traceback.format_exc()
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error": str(exc),
            "type": type(exc).__name__,
            "traceback": tb,
        },
    )


app.include_router(entry.router)
app.include_router(axle.router)
app.include_router(exit_router.router)
app.include_router(db_router.router)


@app.get("/")
def root():
    return {
        "service": "Truck Monitoring API",
        "docs": "/docs",
        "stages": ["Entry ANPR", "Axle Detection", "Exit ANPR"],
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Check API and database. Returns 503 if DB is unreachable."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
