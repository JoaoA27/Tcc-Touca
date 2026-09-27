# =========================
# CÂMERA
# =========================

CAMERA_ID = "camera_01"

CAMERA_INDEX = 0

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30


# =========================
# DETECÇÃO DE PESSOAS
# =========================

YOLO_MODEL = "yolo26n.pt"

YOLO_IMAGE_SIZE = 640

YOLO_CONFIDENCE = 0.40

# COCO classe 0 = person
YOLO_CLASSES = [0]

YOLO_DEVICE = "cpu"


# =========================
# TRACKING
# =========================

TRACKER_CONFIG = "bytetrack.yaml"


# =========================
# DETECÇÃO DE EPI
# =========================

EPI_MODEL = "yoloe-26n-seg.pt"

EPI_IMAGE_SIZE = 640

# Começamos mais baixo porque
# o YOLOE é zero-shot
EPI_CONFIDENCE = 0.20

# Prompts utilizados pelo YOLOE
EPI_CLASSE_JALECO = "white lab coat"
EPI_CLASSE_TOUCA = "bouffant cap"

EPI_CLASSES = [
    EPI_CLASSE_JALECO,
    EPI_CLASSE_TOUCA,
]


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