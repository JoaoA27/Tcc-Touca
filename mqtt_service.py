import json
import uuid

from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from config import (
    CAMERA_ID,
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_KEEPALIVE,
    MQTT_QOS,
    MQTT_TOPIC_PREFIX,
)


class MQTTService:

    def __init__(self):

        self.conectado = False

        # Exemplo:
        # tcc/contagem/camera_01/eventos
        self.topico_eventos = (
            f"{MQTT_TOPIC_PREFIX}/"
            f"{CAMERA_ID}/eventos"
        )

        self.client = mqtt.Client(
            callback_api_version=(
                mqtt.CallbackAPIVersion.VERSION2
            ),
            client_id=f"contador-{CAMERA_ID}",
            protocol=mqtt.MQTTv311,
        )

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    # =========================
    # CALLBACK DE CONEXÃO
    # =========================

    def _on_connect(
        self,
        client,
        userdata,
        flags,
        reason_code,
        properties
    ):

        if reason_code == 0:

            self.conectado = True

            print()
            print("==============================")
            print("MQTT CONECTADO")
            print("==============================")
            print(
                f"Broker: "
                f"{MQTT_BROKER}:{MQTT_PORT}"
            )
            print(
                f"Tópico: "
                f"{self.topico_eventos}"
            )
            print()

        else:

            self.conectado = False

            print(
                f"Erro MQTT. "
                f"Código: {reason_code}"
            )

    # =========================
    # CALLBACK DE DESCONEXÃO
    # =========================

    def _on_disconnect(
        self,
        client,
        userdata,
        disconnect_flags,
        reason_code,
        properties
    ):

        self.conectado = False

        print(
            f"MQTT desconectado. "
            f"Código: {reason_code}"
        )

    # =========================
    # CONECTAR
    # =========================

    def conectar(self):

        try:

            self.client.connect(
                MQTT_BROKER,
                MQTT_PORT,
                MQTT_KEEPALIVE
            )

            # Processamento MQTT em thread separada
            self.client.loop_start()

            return True

        except OSError as erro:

            print()
            print("==============================")
            print("MQTT INDISPONÍVEL")
            print("==============================")
            print(erro)
            print()

            return False

    # =========================
    # PUBLICAR EVENTO
    # =========================

    def publicar_evento(self, evento):

        if not self.conectado:

            print(
                "Evento não enviado: "
                "MQTT desconectado."
            )

            return False

        payload = {
            "event_id": str(uuid.uuid4()),

            "camera_id": CAMERA_ID,

            "tipo": evento["tipo"],

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        mensagem = json.dumps(
            payload,
            ensure_ascii=False
        )

        resultado = self.client.publish(
            topic=self.topico_eventos,
            payload=mensagem,
            qos=MQTT_QOS,
            retain=False,
        )

        if resultado.rc == mqtt.MQTT_ERR_SUCCESS:

            print(
                "MQTT PUBLICADO | "
                f"{mensagem}"
            )

            return True

        print(
            "Erro ao publicar mensagem MQTT."
        )

        return False

    # =========================
    # ENCERRAR
    # =========================

    def fechar(self):

        if self.conectado:
            self.client.disconnect()

        self.client.loop_stop()