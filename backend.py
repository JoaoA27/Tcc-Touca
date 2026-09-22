import json

import paho.mqtt.client as mqtt

from database import Database

from config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_KEEPALIVE,
    MQTT_QOS,
    MQTT_TOPIC_PREFIX,
)


class Backend:

    def __init__(self):

        self.database = Database()

        self.topico = (
            f"{MQTT_TOPIC_PREFIX}/+/eventos"
        )

        self.client = mqtt.Client(
            callback_api_version=(
                mqtt.CallbackAPIVersion.VERSION2
            ),
            client_id="backend-contagem",
            protocol=mqtt.MQTTv311,
        )

        self.client.on_connect = (
            self._on_connect
        )

        self.client.on_message = (
            self._on_message
        )

        self.client.on_disconnect = (
            self._on_disconnect
        )

    # =========================
    # CONECTOU
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

            print()
            print("==============================")
            print("BACKEND MQTT CONECTADO")
            print("==============================")

            print(
                f"Broker: "
                f"{MQTT_BROKER}:{MQTT_PORT}"
            )

            print(
                f"Escutando: "
                f"{self.topico}"
            )

            print()

            self.client.subscribe(
                self.topico,
                qos=MQTT_QOS
            )

        else:

            print(
                f"Erro ao conectar ao MQTT: "
                f"{reason_code}"
            )

    # =========================
    # DESCONECTOU
    # =========================

    def _on_disconnect(
        self,
        client,
        userdata,
        disconnect_flags,
        reason_code,
        properties
    ):

        print(
            f"Backend MQTT desconectado. "
            f"Código: {reason_code}"
        )

    # =========================
    # RECEBEU MENSAGEM
    # =========================

    def _on_message(
        self,
        client,
        userdata,
        message
    ):

        try:

            payload = json.loads(
                message.payload.decode(
                    "utf-8"
                )
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError
        ):

            print(
                "Mensagem MQTT inválida."
            )

            return

        # =========================
        # VALIDAÇÃO
        # =========================

        campos_obrigatorios = (
            "event_id",
            "camera_id",
            "tipo",
            "timestamp",
        )

        for campo in campos_obrigatorios:

            if campo not in payload:

                print(
                    f"Mensagem ignorada: "
                    f"campo '{campo}' ausente."
                )

                return

        if payload["tipo"] not in (
            "entrada",
            "saida"
        ):

            print(
                "Mensagem ignorada: "
                "tipo inválido."
            )

            return

        # =========================
        # BANCO DE DADOS
        # =========================

        inserido = (
            self.database.salvar_evento(
                event_id=payload["event_id"],
                camera_id=payload["camera_id"],
                tipo=payload["tipo"],
                timestamp=payload["timestamp"],
            )
        )

        if inserido:

            print(
                "EVENTO SALVO | "
                f"{payload['camera_id']} | "
                f"{payload['tipo'].upper()} | "
                f"{payload['timestamp']}"
            )

        else:

            print(
                "EVENTO DUPLICADO IGNORADO | "
                f"{payload['event_id']}"
            )

    # =========================
    # EXECUTAR
    # =========================

    def executar(self):

        try:

            self.client.connect(
                MQTT_BROKER,
                MQTT_PORT,
                MQTT_KEEPALIVE
            )

            print(
                "Aguardando eventos..."
            )

            self.client.loop_forever()

        except KeyboardInterrupt:

            print()
            print(
                "Encerrando backend..."
            )

        except OSError as erro:

            print(
                f"Não foi possível conectar "
                f"ao MQTT: {erro}"
            )

        finally:

            self.client.disconnect()


if __name__ == "__main__":

    backend = Backend()

    backend.executar()