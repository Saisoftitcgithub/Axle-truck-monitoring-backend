from datetime import datetime
from core.logger import logger

async def sync_to_ajman(record):
    try:
        logger.info(f"Syncing {record.session_id}")
        return {
            "status": "SUCCESS",
            "time": datetime.utcnow()
        }
        
    except Exception as e:
        logger.exception(f"Sync failed: {e}")
        return {
            "status": "FAILED",
            "time": datetime.utcnow()
        }