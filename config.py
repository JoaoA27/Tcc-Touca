import os

# Diretório base do projeto (independente de onde o comando for executado)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================
# ENTRADA DE VÍDEO / CÂMERA
# =========================

CAMERA_ID = "camera_01"

# Pode ser o índice da webcam (ex: 0, 1) ou o caminho para um arquivo de vídeo (ex: "videos/teste.mp4")
VIDEO_SOURCE = "videos/TesteLab1.mp4"

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30


# =========================
# DETECÇÃO DE PESSOAS
# =========================

YOLO_MODEL = os.path.join(BASE_DIR, "yolo26n.pt")

YOLO_IMAGE_SIZE = 480

YOLO_CONFIDENCE = 0.40

# COCO classe 0 = person
YOLO_CLASSES = [0]

YOLO_DEVICE = "cpu"


# =========================
# TRACKING
# =========================

TRACKER_CONFIG = "bytetrack.yaml"


# =========================
# DETECÇÃO DE EPI (MODELOS DEDICADOS YOLO)
# =========================

MODELO_JALECO = os.path.join(BASE_DIR, "jaleco.pt")
MODELO_TOUCA = os.path.join(BASE_DIR, "touca.pt")

# Resolucao separada: 640 preserva detalhes de gola/lapela do jaleco; 320 acelera e melhora a touca
JALECO_IMAGE_SIZE = 640
TOUCA_IMAGE_SIZE = 320

# Executa o detector pesado de TOUCA (YOLOv12m) a cada N frames, mantendo o JALECO (Nano) em todos os frames
TOUCA_INFERENCIA_INTERVALO = 3

# Confiança para modelos supervisionados dedicados
CONFIDENCIA_JALECO = 0.40
CONFIDENCIA_TOUCA = 0.25

# Validacao cromatica suplementar para evitar falsos positivos de jaleco em camisetas escuras/coloridas
VALIDAR_COR_BRANCA_JALECO = True
JALECO_HSV_MAX_SATURACAO = 65
JALECO_HSV_MIN_BRILHO = 100
JALECO_MIN_PROPORCAO_BRANCO = 0.45

# Índices das classes dentro dos modelos treinados:
# jaleco.pt: {0: 'Gloves', 1: 'Goggles', 2: 'Lab_coat'}
CLASSE_ID_JALECO = 2

# touca.pt: {0: 'hairnet', 1: 'no_hairnet'}
CLASSE_ID_TOUCA = 0



# =========================
# ASSOCIAÇÃO EPI -> PESSOA
# =========================

# Quanto da bounding box do EPI precisa
# estar dentro da bounding box da pessoa
EPI_MIN_OVERLAP_PESSOA = 0.50

# A touca deve estar aproximadamente
# na parte superior da pessoa
TOUCA_MAX_Y_RELATIVO = 0.45

# Região esperada para o jaleco
JALECO_MIN_Y_RELATIVO = 0.10
JALECO_MAX_Y_RELATIVO = 0.95


# =========================
# VERIFICAÇÃO TEMPORAL
# =========================

# Quantidade de frames mantidos no histórico deslizante por track_id
TEMPORAL_WINDOW_SIZE = 20

# Mínimo de frames acumulados antes de emitir diagnóstico consolidado
TEMPORAL_MIN_FRAMES = 8

# Proporção mínima de detecções na janela para confirmar presença de JALECO (ex: 0.60 = 60%)
JALECO_THRESHOLD_RATIO = 0.70

# Proporção mínima de detecções na janela para confirmar presença de TOUCA (ex: 0.30 = 30%)
TOUCA_THRESHOLD_RATIO = 0.30

# Tempo máximo (em segundos) de ausência para descartar o histórico de um track_id
TRACK_MAX_INACTIVE_TIME = 3.0


# =========================
# VISUALIZAÇÃO
# =========================

SHOW_FPS = True

WINDOW_NAME = "Monitoramento de EPI"

DESENHAR_DETECCOES_EPI = True



# =========================
# MQTT
# =========================

# Desligado enquanto desenvolvemos
# a visão computacional
MQTT_ATIVO = False

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_QOS = 1

MQTT_TOPIC_PREFIX = "tcc/epi"


# =========================
# BANCO DE DADOS
# =========================

DATABASE_PATH = "monitoramento_epi.db"