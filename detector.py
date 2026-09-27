from ultralytics import YOLO

from config import (
    YOLO_MODEL,
    YOLO_IMAGE_SIZE,
    YOLO_CONFIDENCE,
    YOLO_CLASSES,
    YOLO_DEVICE,
)


class PersonDetector:

    def __init__(self):

        self.model = YOLO(
            YOLO_MODEL
        )

    def detect(self, frame):

        results = self.model.predict(
            source=frame,
            imgsz=YOLO_IMAGE_SIZE,
            conf=YOLO_CONFIDENCE,
            classes=YOLO_CLASSES,
            device=YOLO_DEVICE,
            verbose=False,
        )

        return results