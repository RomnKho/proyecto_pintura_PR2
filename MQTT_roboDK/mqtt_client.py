import paho.mqtt.client as mqtt

# Configuración por defecto (puedes cambiarla directamente aquí o mediante parámetros)
BROKER = "broker.emqx.io"   # broker público
PORT = 1883
USERNAME = "giirob"
PASSWORD = "UPV2024"

class MQTTManager:
    """
    Gestor centralizado de la conexión MQTT.
    Proporciona publicación, suscripción y gestión del bucle no bloqueante.
    """
    def __init__(self, broker=BROKER, port=PORT, username=None, password=None):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.connected = False

        # Configurar autenticación si se proporcionó
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

    def connect(self):
        """Establece la conexión con el broker y arranca el bucle en segundo plano."""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()   # No bloqueante
            self.connected = True
            print(f"[MQTT] Conectado a {self.broker}:{self.port}")
        except Exception as e:
            print(f"[MQTT] Error de conexión: {e}")
            self.connected = False

    def publish(self, topic, message):
        """Publica un mensaje en el topic especificado."""
        if not self.connected:
            print("[MQTT] No conectado, no se puede publicar.")
            return
        self.client.publish(topic, message)

    def subscribe(self, topic, callback):
        """
        Suscribe un callback específico para un topic.
        El callback debe recibir (client, userdata, msg).
        """
        if not self.connected:
            print("[MQTT] No conectado, no se puede suscribir.")
            return
        self.client.message_callback_add(topic, callback)
        self.client.subscribe(topic)
        print(f"[MQTT] Suscrito a {topic}")

    def set_default_callback(self, callback):
        """Establece el callback por defecto para todos los mensajes."""
        self.client.on_message = callback


# Crear una instancia global única con la configuración deseada
manager = MQTTManager(
    broker=BROKER,
    port=PORT,
    username=USERNAME,   # descomenta si usas autenticación
    password=PASSWORD    # username=None, password=None
)

# Conectar automáticamente al importar el módulo
manager.connect()