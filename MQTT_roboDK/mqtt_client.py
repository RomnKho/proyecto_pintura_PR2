# mqtt_client.py

import paho.mqtt.client as mqtt
import time


BROKER = "broker.emqx.io"
PORT = 1883

USERNAME = "giirob"
PASSWORD = "UPV2024"


class MQTTManager:
    """
    Gestor centralizado de MQTT.
    Sirve para conectar, publicar y suscribirse de forma sencilla.
    """

    def __init__(self, broker=BROKER, port=PORT, username=None, password=None):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password

        # Compatible con versiones nuevas y antiguas de paho-mqtt
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except Exception:
            self.client = mqtt.Client()

        self.connected = False

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        if self.username is not None and self.password is not None:
            self.client.username_pw_set(self.username, self.password)

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        self.connected = True
        print(f"[MQTT] Conectado al broker {self.broker}:{self.port}")

    def _on_disconnect(self, client, userdata, disconnect_flags=None, reason_code=None, properties=None):
        self.connected = False
        print("[MQTT] Desconectado del broker")

    def connect(self):
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()

            # Espera corta hasta conectar
            timeout = time.time() + 5
            while not self.connected and time.time() < timeout:
                time.sleep(0.1)

            return self.connected

        except Exception as e:
            print(f"[MQTT] Error al conectar: {e}")
            return False

    def subscribe(self, topic, callback, qos=0):
        try:
            self.client.message_callback_add(topic, callback)
            self.client.subscribe(topic, qos=qos)
            print(f"[MQTT] Suscrito a {topic}")
            return True

        except Exception as e:
            print(f"[MQTT] Error al suscribirse a {topic}: {e}")
            return False

    def publish(self, topic, payload, qos=0, retain=False):
        try:
            self.client.publish(topic, payload, qos=qos, retain=retain)
            print(f"[MQTT] Publicado en {topic}: {payload}")
            return True

        except Exception as e:
            print(f"[MQTT] Error al publicar en {topic}: {e}")
            return False

    def disconnect(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            print(f"[MQTT] Error al desconectar: {e}")


# Instancia global única
manager = MQTTManager(
    broker=BROKER,
    port=PORT,
    username=None,
    password=None
)

# Conectar automáticamente al importar
manager.connect()