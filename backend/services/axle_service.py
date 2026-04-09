from ultralytics import YOLO
import torch
from torchvision.ops import box_iou
from datetime import datetime
import asyncio

from db.session import SessionLocal
from models.trip import ActiveTrip
from core.logger import logger
from core.config import settings
from services.camera_service import trigger_camera
from services.sync_service import sync_to_ajman
from services.archive_service import move_to_archive

MODEL_PATH = settings.MODEL_PATH

# lazy load model
model = None

def get_model():
    global model
    if model is None:
        model = YOLO(MODEL_PATH)
        logger.info("YOLO model loaded")
    return model

def compute_axle_count(cap):
    model = get_model()
    class_names = model.names

    frame_number = 0
    truck_max_axles = {}

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_number % 3 != 0:
            frame_number += 1
            continue

        results = model.track(
            frame,
            persist=True,
            tracker="botsort.yaml",
            conf=0.6,
            iou=0.5
        )

        trucks = []
        axles = []

        for box in results[0].boxes:
            track_id = int(box.id.item()) if box.id is not None else None
            class_id = int(box.cls.item())
            class_name = class_names[class_id]
            bbox = box.xyxy.tolist()[0]

            if class_name == "truck":
                trucks.append((track_id, bbox))

            elif class_name == "axle":
                axles.append(bbox)

        # Match axles to trucks
        for truck_id, truck_bbox in trucks:
            truck_tensor = torch.tensor([truck_bbox], dtype=torch.float32)

            count = 0
            for axle_bbox in axles:
                axle_tensor = torch.tensor([axle_bbox], dtype=torch.float32)
                iou = box_iou(axle_tensor, truck_tensor)[0][0].item()

                if iou > 0.02:
                    count += 1

            if truck_id not in truck_max_axles:
                truck_max_axles[truck_id] = count
            else:
                truck_max_axles[truck_id] = max(truck_max_axles[truck_id], count)

        frame_number += 1

    cap.release()

    # return max(truck_max_axles.values()) if truck_max_axles else 0
    return list(truck_max_axles.values())[0] if truck_max_axles else 0

def run_axle_detection(session_id: str):
    db = SessionLocal()

    try:
        logger.info(f"Axle detection started: {session_id}")

        cap = trigger_camera()
        axle_count = compute_axle_count(cap)
        trip = db.query(ActiveTrip).filter_by(session_id=session_id).first()
        if not trip:
            logger.error(f"Trip not found: {session_id}")
            return
        
        trip.axle_count = axle_count
        trip.axle_processed_time = datetime.utcnow()
        trip.axle_status = "DONE"
        trip.status = "AXLE_DONE"

        sync = asyncio.run(sync_to_ajman(trip))

        trip.entry_sync_status = sync["status"]
        trip.entry_sync_time = sync["time"]

        db.commit()

        logger.info(f"Axle done: {session_id} → {axle_count}")
        #archive
        if (
            trip.entry_sync_status == "SUCCESS"
            and trip.exit_sync_status == "SUCCESS"
            and trip.axle_status == "DONE"
        ):
            if trip.status != "ARCHIVED": 
                move_to_archive(db, trip)
                logger.info(f"Archived from axle: {trip.session_id}")

    except Exception as e:
        db.rollback() 
        logger.exception(f"Axle detection failed: {e}")

    finally:
        db.close()