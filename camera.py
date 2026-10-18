import cv2
import os

from config import (
    BASE_DIR,
    VIDEO_SOURCE,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FPS,
)


class Camera:

    def __init__(
        self,
        source=VIDEO_SOURCE,
        width=CAMERA_WIDTH,
        height=CAMERA_HEIGHT,
        fps=CAMERA_FPS
    ):
        self.is_file = isinstance(source, str)
        if self.is_file and not os.path.isabs(source) and not os.path.exists(source):
            source = os.path.join(BASE_DIR, source)

        self.source = source

        if self.is_file and not os.path.exists(source):
            raise FileNotFoundError(
                f"Arquivo de vídeo não encontrado: {source}"
            )

        self.cap = cv2.VideoCapture(source)

        if not self.is_file:
            # Configurações válidas principalmente para webcams / streams
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, fps)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Não foi possível abrir a fonte de vídeo: {source}"
            )

    def read(self):
        success, frame = self.cap.read()

        if not success:
            return None

        return frame

    def release(self):
        self.cap.release()