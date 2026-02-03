

from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import init_db
from routes import entry, axle, exit as exit_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup."""
    init_db()
    yield
    # Shutdown: nothing to close for SQLite in this setup


app = FastAPI(
    title="Truck Monitoring API",
    description="Entry ANPR → Axle Detection → Exit ANPR",
    version="1.0.0",
    lifespan=lifespan,
)

# Include modular routers
app.include_router(entry.router)
app.include_router(axle.router)
app.include_router(exit_router.router)


@app.get("/")
def root():
    """Health / info."""
    return {
        "service": "Truck Monitoring API",
        "docs": "/docs",
        "stages": ["Entry ANPR", "Axle Detection", "Exit ANPR"],
    }
