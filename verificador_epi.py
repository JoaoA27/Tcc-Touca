import time
from collections import deque

from config import (
    TEMPORAL_WINDOW_SIZE,
    TEMPORAL_MIN_FRAMES,
    JALECO_THRESHOLD_RATIO,
    TOUCA_THRESHOLD_RATIO,
    TRACK_MAX_INACTIVE_TIME,
)


class EPIVerifier:
    """
    Responsável por realizar a verificação temporal do uso de EPIs (jaleco e touca)
    por meio de uma janela deslizante para cada track_id temporário.
    """

    def __init__(
        self,
        window_size=TEMPORAL_WINDOW_SIZE,
        min_frames=TEMPORAL_MIN_FRAMES,
        jaleco_threshold=JALECO_THRESHOLD_RATIO,
        touca_threshold=TOUCA_THRESHOLD_RATIO,
        max_inactive_time=TRACK_MAX_INACTIVE_TIME,
    ):
        self.window_size = window_size
        self.min_frames = min_frames
        self.jaleco_threshold = jaleco_threshold
        self.touca_threshold = touca_threshold
        self.max_inactive_time = max_inactive_time

        # Estrutura por track_id:
        # {
        #     track_id: {
        #         "jaleco": deque(maxlen=window_size),
        #         "touca": deque(maxlen=window_size),
        #         "ultimo_timestamp": float,
        #         "estado": str
        #     }
        # }
        self.tracks = {}

    def atualizar(self, track_id: int, jaleco_presente: bool, touca_presente: bool) -> dict:
        """
        Adiciona a observação do frame atual ao histórico do track e retorna o diagnóstico consolidado.
        """
        agora = time.time()

        if track_id not in self.tracks:
            self.tracks[track_id] = {
                "jaleco": deque(maxlen=self.window_size),
                "touca": deque(maxlen=self.window_size),
                "ultimo_timestamp": agora,
                "estado": "ANALISANDO",
            }

        track_data = self.tracks[track_id]
        track_data["jaleco"].append(bool(jaleco_presente))
        track_data["touca"].append(bool(touca_presente))
        track_data["ultimo_timestamp"] = agora

        qtd_frames = len(track_data["jaleco"])
        taxa_jaleco = sum(track_data["jaleco"]) / qtd_frames if qtd_frames > 0 else 0.0
        taxa_touca = sum(track_data["touca"]) / qtd_frames if qtd_frames > 0 else 0.0

        # Lógica de decisão temporal
        if qtd_frames < self.min_frames:
            estado = "ANALISANDO"
            jaleco_confirmado = False
            touca_confirmada = False
        else:
            jaleco_confirmado = taxa_jaleco >= self.jaleco_threshold
            if not jaleco_confirmado:
                estado = "SEM_JALECO"
                touca_confirmada = False
            else:
                touca_confirmada = taxa_touca >= self.touca_threshold
                if touca_confirmada:
                    estado = "CONFORME"
                else:
                    estado = "NAO_CONFORME"

        track_data["estado"] = estado

        return {
            "estado": estado,
            "frames_acumulados": qtd_frames,
            "total_janela": self.window_size,
            "taxa_jaleco": taxa_jaleco,
            "taxa_touca": taxa_touca,
            "jaleco_confirmado": jaleco_confirmado,
            "touca_confirmada": touca_confirmada,
        }

    def obter_status(self, track_id: int):
        """Retorna o estado atual gravado para determinado track_id."""
        if track_id in self.tracks:
            return self.tracks[track_id]["estado"]
        return None

    def limpar_inativos(self, active_track_ids=None) -> list:
        """
        Remove tracks inativos que excederam o tempo limite ou não estão na lista de ativos.
        Retorna a lista de track_ids removidos para sincronização com outros serviços.
        """
        agora = time.time()
        removidos = []

        active_set = set(active_track_ids) if active_track_ids is not None else None

        for track_id, data in list(self.tracks.items()):
            inativo_por_tempo = (agora - data["ultimo_timestamp"]) > self.max_inactive_time
            inativo_por_ausencia = (active_set is not None) and (track_id not in active_set)

            # Remove se estourou o tempo de tolerância
            if inativo_por_tempo:
                removidos.append(track_id)
                del self.tracks[track_id]

        return removidos
