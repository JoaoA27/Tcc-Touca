import cv2
import time

from camera import Camera
from detector import PersonDetector
from tracker import PersonTracker

from config import (
    WINDOW_NAME,
    SHOW_FPS,
)


def main():

    # =========================
    # INICIALIZAÇÃO
    # =========================

    camera = Camera()

    detector = PersonDetector()

    tracker = PersonTracker(
        detector
    )

    previous_time = time.time()

    try:

        while True:

            frame = camera.read()

            if frame is None:
                break

            # =========================
            # PESSOA + BYTETRACK
            # =========================

            results = tracker.track(
                frame
            )

            annotated_frame = frame.copy()

            boxes = results[0].boxes

            if boxes is not None:

                for box in boxes:

                    # =========================
                    # TRACK ID
                    # =========================

                    if box.id is not None:

                        track_id = int(
                            box.id.item()
                        )

                    else:

                        track_id = None

                    # =========================
                    # BOUNDING BOX
                    # =========================

                    x1, y1, x2, y2 = (
                        box.xyxy[0].tolist()
                    )

                    x1 = int(x1)
                    y1 = int(y1)
                    x2 = int(x2)
                    y2 = int(y2)

                    # =========================
                    # DESENHA PESSOA
                    # =========================

                    cv2.rectangle(
                        annotated_frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2
                    )

                    cv2.putText(
                        annotated_frame,
                        f"Pessoa | ID {track_id}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )

            # =========================
            # FPS
            # =========================

            if SHOW_FPS:

                current_time = time.time()

                fps = 1 / max(
                    current_time - previous_time,
                    1e-6
                )

                previous_time = (
                    current_time
                )

                cv2.putText(
                    annotated_frame,
                    f"FPS: {fps:.1f}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )

            # =========================
            # VISUALIZAÇÃO
            # =========================

            cv2.imshow(
                WINDOW_NAME,
                annotated_frame
            )

            if (
                cv2.waitKey(1) & 0xFF
                ==
                ord("q")
            ):

                break

    finally:

        camera.release()

        cv2.destroyAllWindows()


if __name__ == "__main__":

    main()