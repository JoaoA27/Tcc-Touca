# =========================
# CÂMERA
# =========================

# Nome da câmera dentro do sistema
CAMERA_ID = "camera_01"

# Índice utilizado pelo OpenCV
CAMERA_INDEX = 0

# Configuração de captura
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30


# =========================
# YOLO
# =========================

YOLO_MODEL = "yolo26n.pt"

# Resolução utilizada na inferência
YOLO_IMAGE_SIZE = 640

# Confiança mínima da detecção
YOLO_CONFIDENCE = 0.40

# Classe 0 do COCO = person
YOLO_CLASSES = [0]

# CPU por enquanto
YOLO_DEVICE = "cpu"


# =========================
# CONTAGEM
# =========================

# Tempo mínimo que a pessoa deve permanecer
# na zona antes de ser considerada válida
TEMPO_MINIMO_ZONA = 0.7

# Posição vertical do ponto de referência:
# 0.0 = topo
# 0.5 = centro
# 1.0 = parte inferior
PONTO_REFERENCIA_Y = 0.50

# Arquivo onde cada câmera guarda
# sua própria zona e linha
ARQUIVO_CONFIG_CAMERAS = "camera_config.json"


# =========================
# VISUALIZAÇÃO
# =========================

SHOW_FPS = True

WINDOW_NAME = "Sistema de Contagem de Pessoas"

# =========================
# BOT-SORT
# =========================

TRACKER_CONFIG = "botsort.yaml"

# Ativar ou desativar Re-ID
BOT_SORT_REID = False

# =========================
# CONTADOR
# =========================

# Direção considerada ENTRADA.
# Se ficar invertido na sua câmera,
# troque para (1, -1).
SENTIDO_ENTRADA = (-1, 1)

# Pequena tolerância caso o ponto da pessoa
# oscile para fora da zona por alguns frames.
TEMPO_TOLERANCIA_FORA_ZONA = 0.5

# Tempo para apagar da memória do contador
# IDs que desapareceram completamente.
TIMEOUT_TRACK_CONTADOR = 5.0

# =========================
# MQTT
# =========================

# Permite desligar o MQTT para testes
MQTT_ATIVO = True

# Broker
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

# Tempo máximo entre comunicações
MQTT_KEEPALIVE = 60

# Qualidade de serviço
MQTT_QOS = 1

# Prefixo dos tópicos
MQTT_TOPIC_PREFIX = "tcc/contagem"