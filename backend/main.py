from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from database import init_db
from routes import entry, axle, exit as exit_router
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

app.include_router(entry.router)
app.include_router(axle.router)
app.include_router(exit_router.router)


@app.get("/")
def root():
    return {
        "service": "Truck Monitoring API",
        "docs": "/docs",
        "stages": ["Entry ANPR", "Axle Detection", "Exit ANPR"],
    }
