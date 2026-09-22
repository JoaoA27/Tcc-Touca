import cv2
import time

from camera import Camera
from detector import PersonDetector
from zonas import ZonaContagem
from tracker import PersonTracker
from contador import ContadorPessoas
from mqtt_service import MQTTService

from config import (
    WINDOW_NAME,
    SHOW_FPS,
    CAMERA_ID,
    MQTT_ATIVO,
)


def main():

    # =========================
    # INICIALIZAÇÃO
    # =========================

    camera = Camera()

    detector = PersonDetector()

    tracker = PersonTracker(detector)

    zona = ZonaContagem(
        camera_id=CAMERA_ID
    )

    contador = ContadorPessoas(
        tempo_minimo_zona=zona.tempo_minimo_zona
    )
    mqtt_service = None

    if MQTT_ATIVO:

        mqtt_service = MQTTService()

        mqtt_service.conectar()

    previous_time = time.time()

    try:

        while True:

            frame = camera.read()

            if frame is None:
                break

            # =========================
            # YOLO + BOT-SORT
            # =========================

            results = tracker.track(frame)

            annotated_frame = results[0].plot()

            # =========================
            # ZONA
            # =========================

            zona.desenhar(
                annotated_frame
            )

            # =========================
            # PESSOAS
            # =========================

            boxes = results[0].boxes

            if boxes is not None:

                for box in boxes:

                    # =========================
                    # TRACK ID
                    # =========================

                    if box.id is not None:
                        track_id = int(box.id.item())
                    else:
                        track_id = None

                    # =========================
                    # BOUNDING BOX
                    # =========================

                    x1, y1, x2, y2 = (
                        box.xyxy[0].tolist()
                    )

                    # =========================
                    # PONTO DE REFERÊNCIA
                    # =========================

                    ponto_x = int(
                        (x1 + x2) / 2
                    )

                    ponto_y = int(
                        y1
                        +
                        (y2 - y1)
                        *
                        zona.ponto_referencia_y
                    )

                    ponto = (
                        ponto_x,
                        ponto_y
                    )

                    # =========================
                    # ESTÁ NA ZONA?
                    # =========================

                    dentro = zona.ponto_dentro(
                        annotated_frame,
                        ponto
                    )

                    # =========================
                    # LADO DA LINHA
                    # =========================

                    lado = zona.lado_da_linha(
                        annotated_frame,
                        ponto
                    )

                    # =========================
                    # CONTADOR
                    # =========================

                    if track_id is not None:

                        evento = contador.atualizar(
                            track_id=track_id,
                            dentro=dentro,
                            lado=lado
                        )

                        # Evento de entrada ou saída
                        if evento is not None:

                            print(
                                f"{evento['tipo'].upper()} | "
                                f"ID: {evento['track_id']} | "
                                f"{evento['lado_origem']} -> "
                                f"{evento['lado_destino']} | "
                                f"Tempo zona: "
                                f"{evento['tempo_zona']}s"
                            )

                            if (
                                MQTT_ATIVO
                                and mqtt_service is not None
                            ):

                                mqtt_service.publicar_evento(
                                    evento
                                )

                    # =========================
                    # VISUALIZAÇÃO DA PESSOA
                    # =========================

                    if dentro:

                        cor = (
                            0,
                            255,
                            0
                        )

                        status = (
                            f"ID {track_id} | "
                            f"DENTRO | "
                            f"lado: {lado}"
                        )

                    else:

                        cor = (
                            0,
                            0,
                            255
                        )

                        status = (
                            f"ID {track_id} | "
                            f"FORA | "
                            f"lado: {lado}"
                        )

                    # Ponto de referência
                    cv2.circle(
                        annotated_frame,
                        ponto,
                        7,
                        cor,
                        -1
                    )

                    # Texto da pessoa
                    cv2.putText(
                        annotated_frame,
                        status,
                        (
                            ponto_x + 10,
                            ponto_y
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        cor,
                        2
                    )

            # =========================
            # LIMPEZA DE TRACKS ANTIGOS
            # =========================

            contador.limpar_tracks_antigos()

            # =========================
            # FPS
            # =========================

            if SHOW_FPS:

                current_time = time.time()

                fps = 1 / max(
                    current_time - previous_time,
                    1e-6
                )

                previous_time = current_time

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
            # CONTADORES NA TELA
            # =========================

            cv2.putText(
                annotated_frame,
                f"Entradas: {contador.entradas}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.putText(
                annotated_frame,
                f"Saidas: {contador.saidas}",
                (20, 115),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

            # Ocupação provisória
            ocupacao = (
                contador.entradas
                -
                contador.saidas
            )

            cv2.putText(
                annotated_frame,
                f"Ocupacao: {ocupacao}",
                (20, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            # =========================
            # MOSTRA
            # =========================

            cv2.imshow(
                WINDOW_NAME,
                annotated_frame
            )

            # Q encerra
            if (
                cv2.waitKey(1) & 0xFF
                ==
                ord("q")
            ):
                break

    finally:
        if mqtt_service is not None:
            mqtt_service.fechar()

        camera.release()

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()