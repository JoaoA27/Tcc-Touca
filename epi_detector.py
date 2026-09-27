from ultralytics import YOLOE

from config import (
    EPI_MODEL,
    EPI_IMAGE_SIZE,
    EPI_CONFIDENCE,
    EPI_CLASSES,
    EPI_CLASSE_JALECO,
    EPI_CLASSE_TOUCA,
    EPI_MIN_OVERLAP_PESSOA,
    TOUCA_MAX_Y_RELATIVO,
    JALECO_MIN_Y_RELATIVO,
    JALECO_MAX_Y_RELATIVO,
    YOLO_DEVICE,
)


class EPIDetector:

    def __init__(self):

        print()
        print("==============================")
        print("CARREGANDO DETECTOR DE EPI")
        print("==============================")

        self.model = YOLOE(
            EPI_MODEL
        )

        self.model.set_classes(
            EPI_CLASSES
        )

        print(
            f"Classes: {EPI_CLASSES}"
        )

        print()

    # =====================================================
    # DETECTAR EPI
    # =====================================================

    def detectar(self, frame):

        resultados = self.model.predict(
            source=frame,
            imgsz=EPI_IMAGE_SIZE,
            conf=EPI_CONFIDENCE,
            device=YOLO_DEVICE,
            verbose=False,
        )

        deteccoes = []

        if not resultados:
            return deteccoes

        resultado = resultados[0]

        if resultado.boxes is None:
            return deteccoes

        for box in resultado.boxes:

            classe_id = int(
                box.cls.item()
            )

            confianca = float(
                box.conf.item()
            )

            if (
                classe_id < 0
                or classe_id >= len(EPI_CLASSES)
            ):
                continue

            classe = EPI_CLASSES[
                classe_id
            ]

            x1, y1, x2, y2 = (
                box.xyxy[0].tolist()
            )

            bbox = (
                int(x1),
                int(y1),
                int(x2),
                int(y2),
            )

            if classe == EPI_CLASSE_JALECO:

                tipo = "jaleco"

            elif classe == EPI_CLASSE_TOUCA:

                tipo = "touca"

            else:

                continue

            deteccoes.append(
                {
                    "tipo": tipo,
                    "classe": classe,
                    "confianca": confianca,
                    "bbox": bbox,
                }
            )

        return deteccoes

    # =====================================================
    # INTERSEÇÃO
    # =====================================================

    def _calcular_overlap(
        self,
        bbox_epi,
        bbox_pessoa
    ):

        ex1, ey1, ex2, ey2 = bbox_epi

        px1, py1, px2, py2 = bbox_pessoa

        ix1 = max(ex1, px1)
        iy1 = max(ey1, py1)

        ix2 = min(ex2, px2)
        iy2 = min(ey2, py2)

        largura = max(
            0,
            ix2 - ix1
        )

        altura = max(
            0,
            iy2 - iy1
        )

        area_intersecao = (
            largura * altura
        )

        area_epi = max(
            1,
            (ex2 - ex1)
            *
            (ey2 - ey1)
        )

        return (
            area_intersecao
            /
            area_epi
        )

    # =====================================================
    # POSIÇÃO RELATIVA
    # =====================================================

    def _posicao_y_relativa(
        self,
        bbox_epi,
        bbox_pessoa
    ):

        _, ey1, _, ey2 = bbox_epi

        _, py1, _, py2 = bbox_pessoa

        centro_y_epi = (
            ey1 + ey2
        ) / 2

        altura_pessoa = max(
            1,
            py2 - py1
        )

        return (
            centro_y_epi - py1
        ) / altura_pessoa

    # =====================================================
    # CENTRO DO EPI DENTRO DA PESSOA
    # =====================================================

    def _centro_dentro_pessoa(
        self,
        bbox_epi,
        bbox_pessoa
    ):

        ex1, ey1, ex2, ey2 = bbox_epi

        px1, py1, px2, py2 = bbox_pessoa

        centro_x = (
            ex1 + ex2
        ) / 2

        centro_y = (
            ey1 + ey2
        ) / 2

        return (
            px1 <= centro_x <= px2
            and
            py1 <= centro_y <= py2
        )

    # =====================================================
    # VALIDAR POSIÇÃO DO EPI
    # =====================================================

    def _posicao_valida(
        self,
        tipo,
        bbox_epi,
        bbox_pessoa
    ):

        y_relativo = (
            self._posicao_y_relativa(
                bbox_epi,
                bbox_pessoa
            )
        )

        if tipo == "touca":

            return (
                y_relativo
                <=
                TOUCA_MAX_Y_RELATIVO
            )

        if tipo == "jaleco":

            return (
                JALECO_MIN_Y_RELATIVO
                <=
                y_relativo
                <=
                JALECO_MAX_Y_RELATIVO
            )

        return False

    # =====================================================
    # ASSOCIAR EPI À PESSOA
    # =====================================================

    def associar(
        self,
        pessoas,
        deteccoes_epi
    ):

        status_pessoas = {}

        # Inicializa todas as pessoas
        for pessoa in pessoas:

            track_id = pessoa["track_id"]

            status_pessoas[track_id] = {
                "jaleco": False,
                "touca": False,

                "confianca_jaleco": 0.0,
                "confianca_touca": 0.0,
            }

        # Analisa cada EPI encontrado
        for deteccao in deteccoes_epi:

            bbox_epi = deteccao["bbox"]

            tipo = deteccao["tipo"]

            melhor_pessoa = None
            melhor_overlap = 0.0

            for pessoa in pessoas:

                bbox_pessoa = (
                    pessoa["bbox"]
                )

                # Centro precisa estar
                # dentro da pessoa
                if not self._centro_dentro_pessoa(
                    bbox_epi,
                    bbox_pessoa
                ):
                    continue

                # Valida posição vertical
                if not self._posicao_valida(
                    tipo,
                    bbox_epi,
                    bbox_pessoa
                ):
                    continue

                overlap = (
                    self._calcular_overlap(
                        bbox_epi,
                        bbox_pessoa
                    )
                )

                if (
                    overlap
                    <
                    EPI_MIN_OVERLAP_PESSOA
                ):
                    continue

                if overlap > melhor_overlap:

                    melhor_overlap = overlap

                    melhor_pessoa = pessoa

            # Nenhuma pessoa compatível
            if melhor_pessoa is None:
                continue

            track_id = (
                melhor_pessoa["track_id"]
            )

            confianca = (
                deteccao["confianca"]
            )

            # =========================
            # JALECO
            # =========================

            if tipo == "jaleco":

                if (
                    confianca
                    >
                    status_pessoas[
                        track_id
                    ][
                        "confianca_jaleco"
                    ]
                ):

                    status_pessoas[
                        track_id
                    ][
                        "jaleco"
                    ] = True

                    status_pessoas[
                        track_id
                    ][
                        "confianca_jaleco"
                    ] = confianca

            # =========================
            # TOUCA
            # =========================

            elif tipo == "touca":

                if (
                    confianca
                    >
                    status_pessoas[
                        track_id
                    ][
                        "confianca_touca"
                    ]
                ):

                    status_pessoas[
                        track_id
                    ][
                        "touca"
                    ] = True

                    status_pessoas[
                        track_id
                    ][
                        "confianca_touca"
                    ] = confianca

        return status_pessoas