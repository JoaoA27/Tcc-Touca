import cv2

from config import (
    CAMERA_INDEX,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FPS,
)


class Camera:

    def __init__(
        self,
        index=CAMERA_INDEX,
        width=CAMERA_WIDTH,
        height=CAMERA_HEIGHT,
        fps=CAMERA_FPS
    ):

        self.cap = cv2.VideoCapture(index)

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            width
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            height
        )

        self.cap.set(
            cv2.CAP_PROP_FPS,
            fps
        )

        if not self.cap.isOpened():
            raise RuntimeError(
                "Não foi possível abrir a câmera."
            )

    def read(self):

        success, frame = self.cap.read()

        if not success:
            return None

        return frame

    def release(self):

        self.cap.release()