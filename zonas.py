import cv2
import json
import os
import numpy as np

from config import (
    CAMERA_ID,
    ARQUIVO_CONFIG_CAMERAS,
)


class ZonaContagem:

    def __init__(self, camera_id=CAMERA_ID):
        self.camera_id = camera_id

        self.zona_normalizada = []
        self.linha_normalizada = []
        self.tempo_minimo_zona = 0.0
        self.ponto_referencia_y = 0.50

        self.carregar_configuracao()

    # =====================================================
    # CARREGAR CONFIGURAÇÃO
    # =====================================================

    def carregar_configuracao(self):

        if not os.path.exists(ARQUIVO_CONFIG_CAMERAS):
            raise FileNotFoundError(
                f"Arquivo '{ARQUIVO_CONFIG_CAMERAS}' não encontrado. "
                f"Execute primeiro o configurador_zona.py."
            )

        with open(
            ARQUIVO_CONFIG_CAMERAS,
            "r",
            encoding="utf-8"
        ) as arquivo:

            configuracoes = json.load(arquivo)

        if self.camera_id not in configuracoes:
            raise ValueError(
                f"A câmera '{self.camera_id}' "
                f"não possui configuração salva."
            )

        config_camera = configuracoes[self.camera_id]

        self.zona_normalizada = config_camera["zona"]
        self.linha_normalizada = config_camera["linha"]

        self.tempo_minimo_zona = config_camera.get(
            "tempo_minimo_zona",
            0.7
        )

        self.ponto_referencia_y = config_camera.get(
            "ponto_referencia_y",
            0.50
        )

        print()
        print("==============================")
        print("CONFIGURAÇÃO DA ZONA CARREGADA")
        print("==============================")
        print(f"Câmera: {self.camera_id}")
        print(
            f"Tempo mínimo: "
            f"{self.tempo_minimo_zona}s"
        )
        print(
            f"Ponto de referência Y: "
            f"{self.ponto_referencia_y}"
        )
        print()

    # =====================================================
    # CONVERSÃO DE COORDENADAS
    # =====================================================

    def _normalizado_para_pixel(
        self,
        ponto,
        largura,
        altura
    ):

        x_normalizado, y_normalizado = ponto

        x = int(x_normalizado * largura)
        y = int(y_normalizado * altura)

        return x, y

    # =====================================================
    # ZONA EM PIXELS
    # =====================================================

    def obter_zona_pixels(self, frame):

        altura, largura = frame.shape[:2]

        pontos = []

        for ponto in self.zona_normalizada:

            ponto_pixel = self._normalizado_para_pixel(
                ponto,
                largura,
                altura
            )

            pontos.append(ponto_pixel)

        return np.array(
            pontos,
            dtype=np.int32
        )

    # =====================================================
    # LINHA EM PIXELS
    # =====================================================

    def obter_linha_pixels(self, frame):

        altura, largura = frame.shape[:2]

        ponto_1 = self._normalizado_para_pixel(
            self.linha_normalizada[0],
            largura,
            altura
        )

        ponto_2 = self._normalizado_para_pixel(
            self.linha_normalizada[1],
            largura,
            altura
        )

        return ponto_1, ponto_2

    # =====================================================
    # VERIFICAR SE PONTO ESTÁ NA ZONA
    # =====================================================

    def ponto_dentro(self, frame, ponto):

        zona = self.obter_zona_pixels(frame)

        resultado = cv2.pointPolygonTest(
            zona,
            ponto,
            False
        )

        return resultado >= 0

    # =====================================================
    # IDENTIFICAR LADO DA LINHA
    # =====================================================

    def lado_da_linha(self, frame, ponto):

        ponto_1, ponto_2 = self.obter_linha_pixels(frame)

        x1, y1 = ponto_1
        x2, y2 = ponto_2

        px, py = ponto

        resultado = (
            (x2 - x1) * (py - y1)
            -
            (y2 - y1) * (px - x1)
        )

        if resultado > 0:
            return 1

        elif resultado < 0:
            return -1

        return 0

    # =====================================================
    # DESENHAR ZONA
    # =====================================================

    def desenhar(self, frame):

        zona = self.obter_zona_pixels(frame)

        # Zona
        cv2.polylines(
            frame,
            [zona],
            True,
            (255, 255, 0),
            2
        )

        # Linha
        ponto_1, ponto_2 = self.obter_linha_pixels(frame)

        cv2.line(
            frame,
            ponto_1,
            ponto_2,
            (0, 0, 255),
            3
        )

        cv2.putText(
            frame,
            "ZONA DE CONTAGEM",
            tuple(zona[0]),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )

        return frame