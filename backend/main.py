from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from db.session import engine
from db.base import Base

from models import trip  

from routes import entry, exit
from core.logger import logger
app = FastAPI()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    logger.info("Tables ready")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"message": "Internal Error"})

app.include_router(entry.router)
app.include_router(exit.router)

@app.get("/")
def root():
    return {"message": "API running"}