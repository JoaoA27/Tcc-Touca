from config import (
    TRACKER_CONFIG,
    YOLO_IMAGE_SIZE,
    YOLO_CONFIDENCE,
    YOLO_CLASSES,
    YOLO_DEVICE,
)


class PersonTracker:

    def __init__(self, detector):

        self.model = detector.model

    def track(self, frame):

        results = self.model.track(
            source=frame,
            persist=True,
            tracker=TRACKER_CONFIG,
            imgsz=YOLO_IMAGE_SIZE,
            conf=YOLO_CONFIDENCE,
            classes=YOLO_CLASSES,
            device=YOLO_DEVICE,
            verbose=False,
        )

        return results