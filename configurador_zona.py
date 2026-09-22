import cv2
import json
import os

from config import (
    CAMERA_ID,
    CAMERA_INDEX,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FPS,
    TEMPO_MINIMO_ZONA,
    PONTO_REFERENCIA_Y,
    ARQUIVO_CONFIG_CAMERAS,
)

WINDOW_NAME = "Configuracao da Zona"

pontos_zona = []
pontos_linha = []

etapa = "zona"

frame_base = None


def mouse_callback(event, x, y, flags, param):
    global etapa

    if event != cv2.EVENT_LBUTTONDOWN:
        return

    # =========================
    # DEFINIÇÃO DA ZONA
    # =========================
    if etapa == "zona":
        pontos_zona.append((x, y))

    # =========================
    # DEFINIÇÃO DA LINHA
    # =========================
    elif etapa == "linha":

        if len(pontos_linha) < 2:
            pontos_linha.append((x, y))


def normalizar_ponto(ponto, largura, altura):
    x, y = ponto

    return [
        round(x / largura, 6),
        round(y / altura, 6),
    ]


def salvar_configuracao(frame):
    altura, largura = frame.shape[:2]

    if len(pontos_zona) < 3:
        print("ERRO: A zona precisa ter pelo menos 3 pontos.")
        return False

    if len(pontos_linha) != 2:
        print("ERRO: A linha precisa ter exatamente 2 pontos.")
        return False

    # Carrega arquivo existente
    if os.path.exists(ARQUIVO_CONFIG_CAMERAS):

        try:
            with open(
                ARQUIVO_CONFIG_CAMERAS,
                "r",
                encoding="utf-8"
            ) as arquivo:

                configuracoes = json.load(arquivo)

        except (json.JSONDecodeError, OSError):
            configuracoes = {}

    else:
        configuracoes = {}

    zona_normalizada = [
        normalizar_ponto(
            ponto,
            largura,
            altura
        )
        for ponto in pontos_zona
    ]

    linha_normalizada = [
        normalizar_ponto(
            ponto,
            largura,
            altura
        )
        for ponto in pontos_linha
    ]

    configuracoes[CAMERA_ID] = {
        "camera_index": CAMERA_INDEX,

        "zona": zona_normalizada,

        "linha": linha_normalizada,

        "tempo_minimo_zona": TEMPO_MINIMO_ZONA,
        
        "ponto_referencia_y": PONTO_REFERENCIA_Y
    }

    with open(
        ARQUIVO_CONFIG_CAMERAS,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            configuracoes,
            arquivo,
            indent=4,
            ensure_ascii=False
        )

    print()
    print("==============================")
    print("CONFIGURACAO SALVA")
    print("==============================")
    print(f"Camera: {CAMERA_ID}")
    print(f"Arquivo: {ARQUIVO_CONFIG_CAMERAS}")
    print()

    return True


def desenhar_interface(frame):
    imagem = frame.copy()

    # =========================
    # DESENHA ZONA
    # =========================

    for ponto in pontos_zona:

        cv2.circle(
            imagem,
            ponto,
            6,
            (255, 255, 0),
            -1
        )

    if len(pontos_zona) >= 2:

        for i in range(
            len(pontos_zona) - 1
        ):

            cv2.line(
                imagem,
                pontos_zona[i],
                pontos_zona[i + 1],
                (255, 255, 0),
                2
            )

    # Fecha visualmente o polígono
    # depois que a zona foi confirmada
    if etapa != "zona" and len(pontos_zona) >= 3:

        cv2.line(
            imagem,
            pontos_zona[-1],
            pontos_zona[0],
            (255, 255, 0),
            2
        )

    # =========================
    # DESENHA LINHA
    # =========================

    for ponto in pontos_linha:

        cv2.circle(
            imagem,
            ponto,
            7,
            (0, 0, 255),
            -1
        )

    if len(pontos_linha) == 2:

        cv2.line(
            imagem,
            pontos_linha[0],
            pontos_linha[1],
            (0, 0, 255),
            3
        )

    # =========================
    # INSTRUÇÕES
    # =========================

    if etapa == "zona":

        texto = (
            "ZONA: clique nos pontos | "
            "ENTER = confirmar"
        )

    elif etapa == "linha":

        texto = (
            "LINHA: clique em 2 pontos | "
            "S = salvar"
        )

    else:

        texto = "Configuracao pronta"

    cv2.rectangle(
        imagem,
        (0, 0),
        (imagem.shape[1], 45),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        imagem,
        texto,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    # Segunda linha de ajuda

    cv2.putText(
        imagem,
        "R = reiniciar | BACKSPACE = desfazer | Q = sair",
        (10, imagem.shape[0] - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    return imagem


def main():
    global etapa
    global frame_base

    camera = cv2.VideoCapture(CAMERA_INDEX)

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT
    )

    camera.set(
        cv2.CAP_PROP_FPS,
        CAMERA_FPS
    )

    if not camera.isOpened():
        raise RuntimeError(
            "Nao foi possivel abrir a camera."
        )

    # Captura alguns frames para a câmera estabilizar
    for _ in range(10):
        sucesso, frame_base = camera.read()

    camera.release()

    if frame_base is None:
        raise RuntimeError(
            "Nao foi possivel capturar imagem da camera."
        )

    cv2.namedWindow(WINDOW_NAME)

    cv2.setMouseCallback(
        WINDOW_NAME,
        mouse_callback
    )

    print()
    print("==============================")
    print("CONFIGURADOR DA ZONA")
    print("==============================")
    print(f"Camera: {CAMERA_ID}")
    print()
    print("1 - Clique para criar a zona")
    print("2 - ENTER confirma a zona")
    print("3 - Clique em 2 pontos para criar a linha")
    print("4 - S salva")
    print()
    print("BACKSPACE = desfazer")
    print("R = reiniciar")
    print("Q = sair")
    print()

    while True:

        imagem = desenhar_interface(
            frame_base
        )

        cv2.imshow(
            WINDOW_NAME,
            imagem
        )

        tecla = cv2.waitKey(20) & 0xFF

        # ENTER
        if tecla == 13:

            if etapa == "zona":

                if len(pontos_zona) >= 3:

                    etapa = "linha"

                    print(
                        "Zona confirmada. "
                        "Agora selecione 2 pontos da linha."
                    )

                else:

                    print(
                        "A zona precisa ter "
                        "pelo menos 3 pontos."
                    )

        # S
        elif tecla == ord("s"):

            if etapa == "linha":

                if salvar_configuracao(
                    frame_base
                ):
                    etapa = "pronto"

        # BACKSPACE
        elif tecla == 8:

            if etapa == "zona":

                if pontos_zona:
                    pontos_zona.pop()

            elif etapa == "linha":

                if pontos_linha:
                    pontos_linha.pop()

        # R
        elif tecla == ord("r"):

            pontos_zona.clear()
            pontos_linha.clear()

            etapa = "zona"

            print("Configuracao reiniciada.")

        # Q
        elif tecla == ord("q"):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()