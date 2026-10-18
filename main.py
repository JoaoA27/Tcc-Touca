import cv2
import time

from camera import Camera
from detector import PersonDetector

from tracker import PersonTracker
from epi_detector import EPIDetector
from verificador_epi import EPIVerifier
from event_service import EventService

from config import (
    WINDOW_NAME,
    SHOW_FPS,
    DESENHAR_DETECCOES_EPI,
)


def extrair_pessoas(resultado):
    """
    Extrai lista de pessoas detectadas com seus respectivos track_ids e bboxes.
    """
    pessoas = []
    boxes = resultado.boxes

    if boxes is None:
        return pessoas

    for box in boxes:
        # Pessoas que ainda nao possuem ID de tracking valido
        if box.id is None:
            continue

        track_id = int(box.id.item())
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        pessoas.append({
            "track_id": track_id,
            "bbox": (int(x1), int(y1), int(x2), int(y2)),
        })

    return pessoas


def desenhar_epis(frame, deteccoes):
    """
    Desenha as caixas delimitadoras brutas detectadas pelo YOLOE.
    """
    for deteccao in deteccoes:
        x1, y1, x2, y2 = deteccao["bbox"]
        tipo = deteccao["tipo"]
        confianca = deteccao["confianca"]

        if tipo == "touca":
            cor = (255, 255, 0)
            nome = "TOUCA"
        else:
            cor = (255, 0, 255)
            nome = "JALECO"

        cv2.rectangle(frame, (x1, y1), (x2, y2), cor, 2)
        texto = f"{nome} {confianca:.2f}"
        cv2.putText(
            frame,
            texto,
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            cor,
            2,
        )


def desenhar_pessoa(frame, pessoa, status_temporal, status_frame):
    """
    Renderiza o bounding box da pessoa e as informacoes de conformidade temporal.
    """
    x1, y1, x2, y2 = pessoa["bbox"]
    track_id = pessoa["track_id"]
    estado = status_temporal["estado"]

    # =========================
    # DEFINIR COR E TEXTO DO ESTADO
    # =========================
    if estado == "ANALISANDO":
        cor = (0, 165, 255)  # Laranja
        texto_estado = f"ID {track_id} | ANALISANDO ({status_temporal['frames_acumulados']}/{status_temporal['total_janela']})"
    elif estado == "SEM_JALECO":
        cor = (200, 200, 0)  # Ciano/Amarelado
        texto_estado = f"ID {track_id} | IGNORADO (SEM JALECO)"
    elif estado == "CONFORME":
        cor = (0, 255, 0)    # Verde
        texto_estado = f"ID {track_id} | CONFORME (JALECO + TOUCA)"
    elif estado == "NAO_CONFORME":
        cor = (0, 0, 255)    # Vermelho
        texto_estado = f"ID {track_id} | ALERTA: SEM TOUCA"
    else:
        cor = (255, 255, 255)
        texto_estado = f"ID {track_id}"

    # Bounding box principal da pessoa
    cv2.rectangle(frame, (x1, y1), (x2, y2), cor, 2)

    # Cabecalho de identificacao com fundo solido
    tamanho_texto, _ = cv2.getTextSize(texto_estado, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
    largura_box = max(260, tamanho_texto[0] + 16)
    
    cv2.rectangle(
        frame,
        (x1, max(0, y1 - 26)),
        (min(frame.shape[1], x1 + largura_box), y1),
        cor,
        -1,
    )

    cv2.putText(
        frame,
        texto_estado,
        (x1 + 6, max(18, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (0, 0, 0),
        2,
    )

    # Detalhes das proporcoes temporais e deteccao instantanea
    if estado != "SEM_JALECO":
        taxa_j = status_temporal["taxa_jaleco"] * 100
        taxa_t = status_temporal["taxa_touca"] * 100
        texto_detalhes = f"Jaleco: {taxa_j:.0f}% | Touca: {taxa_t:.0f}%"

        cv2.putText(
            frame,
            texto_detalhes,
            (x1, min(frame.shape[0] - 10, y2 + 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            cor,
            2,
        )


def main():
    print("=========================================")
    print("INICIALIZANDO MONITORAMENTO DE EPI")
    print("=========================================")

    camera = Camera()
    detector_pessoa = PersonDetector()
    tracker = PersonTracker(detector_pessoa)
    detector_epi = EPIDetector()
    verificador_epi = EPIVerifier()
    event_service = EventService()

    previous_time = time.time()

    try:
        while True:
            frame = camera.read()
            if frame is None:
                print("Fim do fluxo de video ou erro na leitura.")
                break

            # 1. Detecao de pessoas + ByteTrack
            resultados_pessoas = tracker.track(frame)
            pessoas = extrair_pessoas(resultados_pessoas[0])
            active_track_ids = [p["track_id"] for p in pessoas]

            # 2. Deteccao de EPIs (YOLOE zero-shot)
            deteccoes_epi = detector_epi.detectar(frame)

            # 3. Associacao espacial (EPI <-> Pessoa)
            status_frame_pessoas = detector_epi.associar(pessoas, deteccoes_epi)

            # 4. Validacao Temporal + Geracao de Eventos
            status_temporais = {}
            for pessoa in pessoas:
                track_id = pessoa["track_id"]
                st_frame = status_frame_pessoas.get(track_id, {"jaleco": False, "touca": False})

                # Atualiza janela deslizante
                diag_temporal = verificador_epi.atualizar(
                    track_id=track_id,
                    jaleco_presente=st_frame["jaleco"],
                    touca_presente=st_frame["touca"],
                )
                status_temporais[track_id] = diag_temporal

                # Dispara evento se confirmada a nao conformidade
                if diag_temporal["estado"] == "NAO_CONFORME":
                    event_service.registrar_sem_touca(track_id)

            # 5. Garbage Collection de tracks inativos
            removidos = verificador_epi.limpar_inativos(active_track_ids=active_track_ids)
            for track_id_removido in removidos:
                event_service.liberar_track(track_id_removido)

            # 6. Renderizacao visual
            annotated_frame = frame.copy()

            if DESENHAR_DETECCOES_EPI:
                desenhar_epis(annotated_frame, deteccoes_epi)

            for pessoa in pessoas:
                t_id = pessoa["track_id"]
                st_temp = status_temporais.get(t_id)
                st_frame = status_frame_pessoas.get(t_id)

                if st_temp is not None and st_frame is not None:
                    desenhar_pessoa(annotated_frame, pessoa, st_temp, st_frame)

            # 7. Exibicao de FPS
            if SHOW_FPS:
                current_time = time.time()
                fps = 1 / max(current_time - previous_time, 1e-6)
                previous_time = current_time

                cv2.putText(
                    annotated_frame,
                    f"FPS: {fps:.1f}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    2,
                )

            cv2.imshow(WINDOW_NAME, annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Execucao finalizada com sucesso.")


if __name__ == "__main__":
    main()