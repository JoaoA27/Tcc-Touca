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
# VISUALIZAÇÃO
# =========================

SHOW_FPS = True

WINDOW_NAME = "Monitoramento de EPI"


# =========================
# MQTT
# =========================

MQTT_ATIVO = False

MQTT_BROKER = "127.0.0.1"

MQTT_PORT = 1883

MQTT_KEEPALIVE = 60

MQTT_QOS = 1

MQTT_TOPIC_PREFIX = "tcc/epi"


# =========================
# BANCO
# =========================

DATABASE_PATH = "monitoramento_epi.db"