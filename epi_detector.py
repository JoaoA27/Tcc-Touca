import threading
import cv2
import numpy as np
from ultralytics import YOLO

from config import (
    MODELO_JALECO,
    MODELO_TOUCA,
    CLASSE_ID_JALECO,
    CLASSE_ID_TOUCA,
    CONFIDENCIA_JALECO,
    CONFIDENCIA_TOUCA,
    JALECO_IMAGE_SIZE,
    TOUCA_IMAGE_SIZE,
    TOUCA_INFERENCIA_INTERVALO,
    VALIDAR_COR_BRANCA_JALECO,
    JALECO_HSV_MAX_SATURACAO,
    JALECO_HSV_MIN_BRILHO,
    JALECO_MIN_PROPORCAO_BRANCO,
    EPI_MIN_OVERLAP_PESSOA,
    TOUCA_MAX_Y_RELATIVO,
    JALECO_MIN_Y_RELATIVO,
    JALECO_MAX_Y_RELATIVO,
    YOLO_DEVICE,
)


class EPIDetector:
    """
    Detector de EPIs baseado em modelos dedicados YOLO (jaleco.pt e touca.pt).
    Responsavel por inferir bounding boxes e associar espacialmente a cada pessoa.
    """

    def __init__(self):
        print("\n==============================")
        print("CARREGANDO MODELOS DE EPI (YOLO)")
        print("==============================")
        print(f"Carregando detector de jaleco: {MODELO_JALECO}")
        self.model_jaleco = YOLO(MODELO_JALECO)
        print(f"Classes jaleco: {self.model_jaleco.names}")

        print(f"Carregando detector de touca: {MODELO_TOUCA}")
        self.model_touca = YOLO(MODELO_TOUCA)
        print(f"Classes touca: {self.model_touca.names}\n")

        self._jaleco_frame_count = 0
        self._ultimos_jalecos = []
        self._touca_frame_count = 0
        self._ultimas_toucas = []
        self._ultimo_frame = None
        self._lock_touca = threading.Lock()
        self._touca_rodando = False

    def _validar_cor_jaleco(self, frame, bbox):
        """
        Verifica se a regiao detectada como jaleco possui predominancia de tons
        claros/brancos no espaco HSV, evitando falsos positivos em camisetas escuras ou coloridas.
        """
        if not VALIDAR_COR_BRANCA_JALECO:
            return True

        h_img, w_img = frame.shape[:2]
        x1, y1, x2, y2 = bbox
        x1 = max(0, min(w_img - 1, x1))
        x2 = max(0, min(w_img, x2))
        y1 = max(0, min(h_img - 1, y1))
        y2 = max(0, min(h_img, y2))

        if x2 - x1 < 10 or y2 - y1 < 10:
            return False

        recorte = frame[y1:y2, x1:x2]
        hsv = cv2.cvtColor(recorte, cv2.COLOR_BGR2HSV)

        # Pixels claros/brancos: baixa saturacao (S) e brilho moderado/alto (V)
        mascara_branco = (hsv[:, :, 1] <= JALECO_HSV_MAX_SATURACAO) & (
            hsv[:, :, 2] >= JALECO_HSV_MIN_BRILHO
        )
        proporcao_branco = float(np.mean(mascara_branco))

        return proporcao_branco >= JALECO_MIN_PROPORCAO_BRANCO

    def _verificar_jaleco_corpo_pessoa(self, frame, bbox_pessoa):
        """
        Complemento para cameras de seguranca (pessoas de costas ou inclinadas no balcao):
        verifica a continuidade do jaleco branco cobrindo TANTO o tronco superior (18% a 48%)
        QUANTO a aba inferior do jaleco sobre o quadril/coxa (48% a 75%).
        """
        h_frame, w_frame = frame.shape[:2]
        px1, py1, px2, py2 = bbox_pessoa
        h_p = py2 - py1
        w_p = px2 - px1

        # Ignora deteccoes muito pequenas no fundo distante (proporcional a resolucao do video)
        if h_p < int(h_frame * 0.24) or w_p < int(w_frame * 0.08):
            return None

        # So aplica quando a base da pessoa nao esta colada na borda inferior (evita close-up de webcam)
        if py2 >= h_frame - 15:
            return None

        sup = frame[
            max(0, int(py1 + h_p * 0.18)) : min(h_frame, int(py1 + h_p * 0.48)),
            max(0, int(px1 + w_p * 0.22)) : min(w_frame, int(px1 + w_p * 0.78)),
        ]
        inf = frame[
            max(0, int(py1 + h_p * 0.48)) : min(h_frame, int(py1 + h_p * 0.75)),
            max(0, int(px1 + w_p * 0.22)) : min(w_frame, int(px1 + w_p * 0.78)),
        ]
        if sup.size == 0 or inf.size == 0:
            return None

        hsv_sup = cv2.cvtColor(sup, cv2.COLOR_BGR2HSV)
        hsv_inf = cv2.cvtColor(inf, cv2.COLOR_BGR2HSV)
        r_sup = float(np.mean((hsv_sup[:, :, 1] <= 60) & (hsv_sup[:, :, 2] >= 105)))
        r_inf = float(np.mean((hsv_inf[:, :, 1] <= 60) & (hsv_inf[:, :, 2] >= 105)))

        if r_sup >= 0.58 and r_inf >= 0.58:
            bbox_jaleco = (
                int(px1 + w_p * 0.10),
                int(py1 + h_p * 0.16),
                int(px2 - w_p * 0.10),
                int(py1 + h_p * 0.78),
            )
            return {
                "tipo": "jaleco",
                "classe": "Lab_coat",
                "confianca": round((r_sup + r_inf) / 2.0, 2),
                "bbox": bbox_jaleco,
            }
        return None

    def _verificar_touca_topo_cabeca(self, frame, bbox_pessoa):
        """
        Complemento para cameras de seguranca (CCTV) quando a pessoa de jaleco inclina
        a cabeca sobre a bancada e o detector de touca perde momentaneamente o contorno.
        """
        h_frame, w_frame = frame.shape[:2]
        px1, py1, px2, py2 = bbox_pessoa
        h_p = py2 - py1
        w_p = px2 - px1

        if h_p < int(h_frame * 0.24) or w_p < int(w_frame * 0.08) or py2 >= h_frame - 15:
            return None

        hx1 = max(0, int(px1 + w_p * 0.25))
        hx2 = min(w_frame, int(px2 - w_p * 0.25))
        hy1 = max(0, int(py1))
        hy2 = min(h_frame, int(py1 + h_p * 0.18))

        if hx2 - hx1 < 8 or hy2 - hy1 < 8:
            return None

        head = frame[hy1:hy2, hx1:hx2]
        hsv_h = cv2.cvtColor(head, cv2.COLOR_BGR2HSV)
        med_s = float(np.median(hsv_h[:, :, 1]))
        med_v = float(np.median(hsv_h[:, :, 2]))
        r_claro = float(np.mean((hsv_h[:, :, 1] <= 48) & (hsv_h[:, :, 2] >= 90)))

        if med_s <= 42.0 and med_v >= 88.0 and r_claro >= 0.40:
            return {
                "tipo": "touca",
                "classe": "hairnet",
                "confianca": round(r_claro, 2),
                "bbox": (hx1, hy1, hx2, hy2),
            }
        return None

    def _inferir_toucas(self, frame, pessoas=None):
        self._touca_frame_count += 1
        if (self._touca_frame_count - 1) % TOUCA_INFERENCIA_INTERVALO != 0 and self._ultimas_toucas:
            return list(self._ultimas_toucas)

        novas_toucas = []
        res_touca = self.model_touca.predict(
            source=frame,
            imgsz=max(480, TOUCA_IMAGE_SIZE),
            conf=CONFIDENCIA_TOUCA,
            device=YOLO_DEVICE,
            verbose=False,
        )

        if res_touca and res_touca[0].boxes is not None:
            for box in res_touca[0].boxes:
                cls_id = int(box.cls.item())
                if cls_id == CLASSE_ID_TOUCA:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    novas_toucas.append({
                        "tipo": "touca",
                        "classe": "hairnet",
                        "confianca": float(box.conf.item()),
                        "bbox": (int(x1), int(y1), int(x2), int(y2)),
                    })

        if pessoas:
            for pessoa in pessoas:
                ja_tem_touca = any(
                    self._centro_dentro_pessoa(t["bbox"], pessoa["bbox"], tipo="touca")
                    for t in novas_toucas
                )
                if not ja_tem_touca:
                    det_t = self._verificar_touca_topo_cabeca(frame, pessoa["bbox"])
                    if det_t is not None:
                        novas_toucas.append(det_t)

        self._ultimas_toucas = novas_toucas
        return list(novas_toucas)

    # =====================================================
    # DETECTAR EPIS (JALECO + TOUCA EM CASCATA)
    # =====================================================

    def detectar(self, frame, pessoas=None):
        self._ultimo_frame = frame

        # Se nao houver pessoas na cena, nao gasta CPU rodando modelos de EPI
        if pessoas is not None and len(pessoas) == 0:
            self._touca_frame_count = 0
            self._ultimas_toucas = []
            return []

        deteccoes = []

        # 1. Inferencia para JALECO no frame completo
        res_jaleco = self.model_jaleco.predict(
            source=frame,
            imgsz=JALECO_IMAGE_SIZE,
            conf=CONFIDENCIA_JALECO,
            device=YOLO_DEVICE,
            verbose=False,
        )

        tem_jaleco = False
        if res_jaleco and res_jaleco[0].boxes is not None:
            for box in res_jaleco[0].boxes:
                cls_id = int(box.cls.item())
                if cls_id == CLASSE_ID_JALECO:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    bbox_int = (int(x1), int(y1), int(x2), int(y2))

                    if not self._validar_cor_jaleco(frame, bbox_int):
                        continue

                    tem_jaleco = True
                    deteccoes.append({
                        "tipo": "jaleco",
                        "classe": "Lab_coat",
                        "confianca": float(box.conf.item()),
                        "bbox": bbox_int,
                    })

        # 1b. Complemento por pessoa rastreada (quando pessoas e passado diretamente)
        if pessoas:
            for pessoa in pessoas:
                ja_tem = any(
                    d["tipo"] == "jaleco" and self._centro_dentro_pessoa(d["bbox"], pessoa["bbox"])
                    for d in deteccoes
                )
                if not ja_tem:
                    det_comp = self._verificar_jaleco_corpo_pessoa(frame, pessoa["bbox"])
                    if det_comp is not None:
                        tem_jaleco = True
                        deteccoes.append(det_comp)

        # 2. Inferencia em cascata para TOUCA (somente se houver jaleco na cena)
        if tem_jaleco:
            deteccoes.extend(self._inferir_toucas(frame, pessoas=pessoas))
        elif pessoas is not None:
            self._touca_frame_count = 0
            self._ultimas_toucas = []

        return deteccoes

    # =====================================================
    # REGRAS GEOMETRICAS DE ASSOCIACAO
    # =====================================================

    def _expandir_topo_pessoa(self, tipo, bbox_pessoa):
        if tipo != "touca":
            return bbox_pessoa
        px1, py1, px2, py2 = bbox_pessoa
        altura = max(1, py2 - py1)
        # Expande 15% para cima pois a touca bufante frequentemente ultrapassa a linha da testa
        novo_py1 = max(0, int(py1 - 0.15 * altura))
        return (px1, novo_py1, px2, py2)

    def _calcular_overlap(self, bbox_epi, bbox_pessoa, tipo="jaleco"):
        ex1, ey1, ex2, ey2 = bbox_epi
        px1, py1, px2, py2 = self._expandir_topo_pessoa(tipo, bbox_pessoa)

        ix1 = max(ex1, px1)
        iy1 = max(ey1, py1)
        ix2 = min(ex2, px2)
        iy2 = min(ey2, py2)

        largura = max(0, ix2 - ix1)
        altura = max(0, iy2 - iy1)
        area_intersecao = largura * altura
        area_epi = max(1, (ex2 - ex1) * (ey2 - ey1))

        return area_intersecao / area_epi

    def _posicao_y_relativa(self, bbox_epi, bbox_pessoa):
        _, ey1, _, ey2 = bbox_epi
        _, py1, _, py2 = bbox_pessoa
        centro_y_epi = (ey1 + ey2) / 2
        altura_pessoa = max(1, py2 - py1)
        return (centro_y_epi - py1) / altura_pessoa

    def _centro_dentro_pessoa(self, bbox_epi, bbox_pessoa, tipo="jaleco"):
        ex1, ey1, ex2, ey2 = bbox_epi
        px1, py1, px2, py2 = self._expandir_topo_pessoa(tipo, bbox_pessoa)
        centro_x = (ex1 + ex2) / 2
        centro_y = (ey1 + ey2) / 2
        return px1 <= centro_x <= px2 and py1 <= centro_y <= py2

    def _posicao_valida(self, tipo, bbox_epi, bbox_pessoa):
        y_rel = self._posicao_y_relativa(bbox_epi, bbox_pessoa)

        if tipo == "touca":
            return -0.15 <= y_rel <= TOUCA_MAX_Y_RELATIVO
        if tipo == "jaleco":
            return JALECO_MIN_Y_RELATIVO <= y_rel <= JALECO_MAX_Y_RELATIVO

        return False

    # =====================================================
    # ASSOCIAR EPIS A CADA PESSOA NO FRAME
    # =====================================================

    def associar(self, pessoas, deteccoes_epi):
        status_pessoas = {}

        # Inicializa status de cada pessoa detectada
        for pessoa in pessoas:
            track_id = pessoa["track_id"]
            status_pessoas[track_id] = {
                "jaleco": False,
                "touca": False,
                "confianca_jaleco": 0.0,
                "confianca_touca": 0.0,
            }

        # Fallback automatico caso detectar(frame) tenha sido chamado sem passar 'pessoas'
        if self._ultimo_frame is not None and pessoas:
            adicionou_jaleco = False
            for pessoa in pessoas:
                ja_tem = any(
                    d["tipo"] == "jaleco" and self._centro_dentro_pessoa(d["bbox"], pessoa["bbox"])
                    for d in deteccoes_epi
                )
                if not ja_tem:
                    det_comp = self._verificar_jaleco_corpo_pessoa(self._ultimo_frame, pessoa["bbox"])
                    if det_comp is not None:
                        deteccoes_epi.append(det_comp)
                        adicionou_jaleco = True

            tem_touca_lista = any(d["tipo"] == "touca" for d in deteccoes_epi)
            if adicionou_jaleco and not tem_touca_lista:
                deteccoes_epi.extend(self._inferir_toucas(self._ultimo_frame, pessoas=pessoas))

            for pessoa in pessoas:
                tem_j_pessoa = any(
                    d["tipo"] == "jaleco" and self._centro_dentro_pessoa(d["bbox"], pessoa["bbox"])
                    for d in deteccoes_epi
                )
                tem_t_pessoa = any(
                    d["tipo"] == "touca" and self._centro_dentro_pessoa(d["bbox"], pessoa["bbox"], tipo="touca")
                    for d in deteccoes_epi
                )
                if tem_j_pessoa and not tem_t_pessoa:
                    det_t = self._verificar_touca_topo_cabeca(self._ultimo_frame, pessoa["bbox"])
                    if det_t is not None:
                        deteccoes_epi.append(det_t)

        # Associa cada EPI encontrado a melhor pessoa compativel
        for deteccao in deteccoes_epi:
            bbox_epi = deteccao["bbox"]
            tipo = deteccao["tipo"]

            melhor_pessoa = None
            melhor_overlap = 0.0

            for pessoa in pessoas:
                bbox_pessoa = pessoa["bbox"]

                if not self._centro_dentro_pessoa(bbox_epi, bbox_pessoa, tipo=tipo):
                    continue

                if not self._posicao_valida(tipo, bbox_epi, bbox_pessoa):
                    continue

                overlap = self._calcular_overlap(bbox_epi, bbox_pessoa, tipo=tipo)
                if overlap < EPI_MIN_OVERLAP_PESSOA:
                    continue

                if overlap > melhor_overlap:
                    melhor_overlap = overlap
                    melhor_pessoa = pessoa

            if melhor_pessoa is None:
                continue

            track_id = melhor_pessoa["track_id"]
            conf = deteccao["confianca"]

            if tipo == "jaleco":
                if conf > status_pessoas[track_id]["confianca_jaleco"]:
                    status_pessoas[track_id]["jaleco"] = True
                    status_pessoas[track_id]["confianca_jaleco"] = conf
            elif tipo == "touca":
                if conf > status_pessoas[track_id]["confianca_touca"]:
                    status_pessoas[track_id]["touca"] = True
                    status_pessoas[track_id]["confianca_touca"] = conf

        return status_pessoas