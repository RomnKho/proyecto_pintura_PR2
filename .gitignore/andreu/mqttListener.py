# mqtt_listener.py
import json
import time
import mqtt_client as mqtt
import generator as g

from robodk import robolink    # RoboDK API
RDK = robolink.Robolink()

topic_sub = "emqx/andreu/sub/gen"
topic_pub = "emqx/andreu/pub/global"

class Payload(object):
    def __init__(self, rgb_hex, tamano, cantidad, tipo, linea):
        self.rgb_hex = rgb_hex
        self.tamano = tamano
        self.cantidad = cantidad
        self.tipo = tipo
        self.linea = linea

def as_payload(dct):
    return Payload(dct['rgb_hex'], dct['tamano'], int(dct['cantidad']), dct['tipo'], dct['linea'])

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    topic = msg.topic
    qos = msg.qos   # si no lo usas, no hace falta

    try:
        desJson = json.loads(payload, object_hook=as_payload)
    except Exception as e:
        print(f"Error al parsear JSON: {e}")
        return

    # Publicar confirmación de recepción
    message_to_pub = f"Cod: {desJson.rgb_hex}, Sz: {desJson.tamano}, q: {desJson.cantidad}, type: {desJson.tipo}"
    print(f"Recibido en {topic}: {message_to_pub}")
    mqtt.manager.publish(topic_pub, message_to_pub)
    print(f"Publicado en {topic_pub}: {message_to_pub}")
    # Llamar a la función de generación (la que encola los pedidos)
    g.handle_message(client, topic, payload)   # pasamos el cliente (aunque no se use dentro)

mqtt.manager.subscribe(topic_sub, on_message)

mqtt.manager.publish(topic_pub, "Ready from RoboDK")

try:
    while True:
        time.sleep(1)   # bucle infinito para que el script no termine
except KeyboardInterrupt:
    print("Cerrando MQTT Listener")