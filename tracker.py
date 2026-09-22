import yaml

from config import (
    TRACKER_CONFIG,
    BOT_SORT_REID,
    YOLO_IMAGE_SIZE,
    YOLO_CONFIDENCE,
    YOLO_CLASSES,
    YOLO_DEVICE,
)


class PersonTracker:

    def __init__(self, detector):

        self.model = detector.model

        self._configurar_reid()

    def _configurar_reid(self):

        with open(
            TRACKER_CONFIG,
            "r",
            encoding="utf-8"
        ) as arquivo:

            config_tracker = yaml.safe_load(arquivo)

        if not config_tracker:
            raise ValueError(
                f"O arquivo '{TRACKER_CONFIG}' está vazio "
                "ou possui uma configuração inválida."
            )

        if "tracker_type" not in config_tracker:
            raise ValueError(
                f"O arquivo '{TRACKER_CONFIG}' não possui "
                "o campo 'tracker_type'."
            )

        config_tracker["with_reid"] = BOT_SORT_REID

        with open(
            TRACKER_CONFIG,
            "w",
            encoding="utf-8"
        ) as arquivo:

            yaml.safe_dump(
                config_tracker,
                arquivo,
                sort_keys=False
            )

        status_reid = (
            "ATIVADO"
            if BOT_SORT_REID
            else "DESATIVADO"
        )

        print(
            f"BoT-SORT Re-ID: {status_reid}"
        )

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