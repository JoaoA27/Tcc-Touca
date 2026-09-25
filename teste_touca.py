import cv2

from ultralytics import YOLOE


modelo = YOLOE(
    "yoloe-26n-seg.pt"
)

modelo.set_classes([
    "hairnet",
    "white hairnet",
    "bouffant cap",
    "surgical cap",
    "white cap",
])


camera = cv2.VideoCapture(0)

if not camera.isOpened():
    raise RuntimeError(
        "Não foi possível abrir a câmera."
    )


while True:

    sucesso, frame = camera.read()

    if not sucesso:
        break

    resultados = modelo.predict(
        frame,
        conf=0.20,
        verbose=False
    )

    frame_anotado = (
        resultados[0].plot()
    )

    cv2.imshow(
        "Teste de Touca",
        frame_anotado
    )

    if (
        cv2.waitKey(1) & 0xFF
        ==
        ord("q")
    ):
        break


camera.release()
cv2.destroyAllWindows()