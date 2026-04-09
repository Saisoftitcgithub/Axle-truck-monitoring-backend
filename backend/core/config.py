from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str
    MODEL_PATH: str
    VIDEO_PATH: str

    class Config:
        env_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  
            ".env"
        )

settings = Settings()