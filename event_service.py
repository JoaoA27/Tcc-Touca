import json
import uuid

from datetime import datetime, timezone

from config import CAMERA_ID


class EventService:

    def __init__(self):

        # Guarda quais eventos já foram
        # gerados para cada track_id.
        #
        # Exemplo:
        # {
        #     7: {"sem_touca"},
        #     9: {"sem_touca"}
        # }
        self.eventos_por_track = {}

    # =====================================================
    # GERAR EVENTO
    # =====================================================

    def gerar_evento(
        self,
        track_id,
        tipo
    ):

        # =========================
        # CONTROLE DE DUPLICIDADE
        # =========================

        if track_id not in self.eventos_por_track:

            self.eventos_por_track[
                track_id
            ] = set()

        eventos_track = (
            self.eventos_por_track[
                track_id
            ]
        )

        # A mesma pessoa não gera
        # novamente o mesmo evento
        if tipo in eventos_track:

            print(
                f"EVENTO IGNORADO | "
                f"ID {track_id} | "
                f"{tipo} já registrado"
            )

            return None

        # =========================
        # ESTRUTURA DO EVENTO
        # =========================

        evento = {
            "event_id": str(
                uuid.uuid4()
            ),

            "camera_id": CAMERA_ID,

            "tipo": tipo,

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        # Marca antes da publicação,
        # evitando gerar duplicados
        eventos_track.add(
            tipo
        )

        # Por enquanto simulamos
        # MQTT / backend / banco
        self._simular_publicacao(
            evento
        )

        return evento

    # =====================================================
    # NÃO CONFORMIDADE
    # =====================================================

    def registrar_sem_touca(
        self,
        track_id
    ):

        return self.gerar_evento(
            track_id=track_id,
            tipo="sem_touca"
        )

    # =====================================================
    # SIMULAÇÃO MQTT / BACKEND
    # =====================================================

    def _simular_publicacao(
        self,
        evento
    ):

        mensagem = json.dumps(
            evento,
            ensure_ascii=False
        )

        print()
        print(
            "=============================="
        )

        print(
            "EVENTO DE NÃO CONFORMIDADE"
        )

        print(
            "=============================="
        )

        print(mensagem)

        print(
            "=============================="
        )

        print()

    # =====================================================
    # LIBERAR TRACK
    # =====================================================

    def liberar_track(
        self,
        track_id
    ):

        if (
            track_id
            in
            self.eventos_por_track
        ):

            del self.eventos_por_track[
                track_id
            ]