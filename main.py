import cv2
import time

from camera import Camera
from detector import PersonDetector
from tracker import PersonTracker
from epi_detector import EPIDetector

from config import (
    WINDOW_NAME,
    SHOW_FPS,
    DESENHAR_DETECCOES_EPI,
)


def extrair_pessoas(resultado):

    pessoas = []

    boxes = resultado.boxes

    if boxes is None:
        return pessoas

    for box in boxes:

        # Ainda sem ID válido
        if box.id is None:
            continue

        track_id = int(
            box.id.item()
        )

        x1, y1, x2, y2 = (
            box.xyxy[0].tolist()
        )

        pessoas.append(
            {
                "track_id": track_id,

                "bbox": (
                    int(x1),
                    int(y1),
                    int(x2),
                    int(y2),
                ),
            }
        )

    return pessoas


# =========================================================
# DESENHAR DETECÇÕES DO YOLOE
# =========================================================

def desenhar_epis(
    frame,
    deteccoes
):

    for deteccao in deteccoes:

        x1, y1, x2, y2 = (
            deteccao["bbox"]
        )

        tipo = deteccao["tipo"]

        confianca = (
            deteccao["confianca"]
        )

        if tipo == "touca":

            cor = (
                255,
                255,
                0
            )

            nome = "TOUCA"

        else:

            cor = (
                255,
                0,
                255
            )

            nome = "JALECO"

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            cor,
            2
        )

        texto = (
            f"{nome} "
            f"{confianca:.2f}"
        )

        cv2.putText(
            frame,
            texto,
            (
                x1,
                max(
                    20,
                    y1 - 10
                )
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            cor,
            2
        )


# =========================================================
# DESENHAR PESSOA + STATUS
# =========================================================

def desenhar_pessoa(
    frame,
    pessoa,
    status
):

    x1, y1, x2, y2 = (
        pessoa["bbox"]
    )

    track_id = (
        pessoa["track_id"]
    )

    jaleco = status["jaleco"]

    touca = status["touca"]

    confianca_jaleco = (
        status["confianca_jaleco"]
    )

    confianca_touca = (
        status["confianca_touca"]
    )

    # =========================
    # DEFINIR STATUS VISUAL
    # =========================

    if not jaleco:

        cor = (
            0,
            255,
            255
        )

        texto = (
            f"ID {track_id} | "
            f"JALECO: NAO"
        )

    elif touca:

        cor = (
            0,
            255,
            0
        )

        texto = (
            f"ID {track_id} | "
            f"JALECO: SIM | "
            f"TOUCA: SIM"
        )

    else:

        cor = (
            0,
            0,
            255
        )

        texto = (
            f"ID {track_id} | "
            f"JALECO: SIM | "
            f"TOUCA: NAO"
        )

    # =========================
    # BOUNDING BOX DA PESSOA
    # =========================

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        cor,
        2
    )

    # Fundo para melhorar leitura
    largura_texto = 430

    cv2.rectangle(
        frame,
        (
            x1,
            max(
                0,
                y1 - 30
            )
        ),
        (
            min(
                frame.shape[1],
                x1 + largura_texto
            ),
            y1
        ),
        cor,
        -1
    )

    cv2.putText(
        frame,
        texto,
        (
            x1 + 5,
            max(
                20,
                y1 - 8
            )
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (
            0,
            0,
            0
        ),
        2
    )

    # =========================
    # CONFIANÇAS
    # =========================

    if jaleco:

        texto_jaleco = (
            f"Jaleco: "
            f"{confianca_jaleco:.2f}"
        )

        cv2.putText(
            frame,
            texto_jaleco,
            (
                x1,
                min(
                    frame.shape[0] - 10,
                    y2 + 20
                )
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            cor,
            2
        )

    if touca:

        texto_touca = (
            f"Touca: "
            f"{confianca_touca:.2f}"
        )

        cv2.putText(
            frame,
            texto_touca,
            (
                x1,
                min(
                    frame.shape[0] - 10,
                    y2 + 40
                )
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            cor,
            2
        )


def main():

    # =========================
    # INICIALIZAÇÃO
    # =========================

    camera = Camera()

    detector_pessoa = (
        PersonDetector()
    )

    tracker = PersonTracker(
        detector_pessoa
    )

    detector_epi = (
        EPIDetector()
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

            resultados_pessoas = (
                tracker.track(
                    frame
                )
            )

            pessoas = extrair_pessoas(
                resultados_pessoas[0]
            )

            # =========================
            # YOLOE - EPI
            # =========================

            deteccoes_epi = (
                detector_epi.detectar(
                    frame
                )
            )

            # =========================
            # ASSOCIAR EPI À PESSOA
            # =========================

            status_pessoas = (
                detector_epi.associar(
                    pessoas,
                    deteccoes_epi
                )
            )

            # =========================
            # IMAGEM
            # =========================

            annotated_frame = (
                frame.copy()
            )

            # Mostra bounding boxes
            # encontradas diretamente
            # pelo YOLOE
            if DESENHAR_DETECCOES_EPI:

                desenhar_epis(
                    annotated_frame,
                    deteccoes_epi
                )

            # =========================
            # MOSTRA CADA PESSOA
            # =========================

            for pessoa in pessoas:

                track_id = (
                    pessoa["track_id"]
                )

                status = (
                    status_pessoas.get(
                        track_id
                    )
                )

                if status is None:
                    continue

                desenhar_pessoa(
                    annotated_frame,
                    pessoa,
                    status
                )

            # =========================
            # FPS
            # =========================

            if SHOW_FPS:

                current_time = (
                    time.time()
                )

                fps = 1 / max(
                    current_time
                    -
                    previous_time,
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
                    (
                        0,
                        255,
                        0
                    ),
                    2
                )

            # =========================
            # MOSTRAR
            # =========================

            cv2.imshow(
                WINDOW_NAME,
                annotated_frame
            )

            if (
                cv2.waitKey(1)
                &
                0xFF
                ==
                ord("q")
            ):

                break

    finally:

        camera.release()

        cv2.destroyAllWindows()


if __name__ == "__main__":

    main()