# Script que handlea todo lo recibido por mqtt

import json
from queue import Queue
from robodk.robolink import *   # RoboDK API
from robodk.robomath import *   # Robot toolbox
from dataclasses import dataclass
import Init

topic_sub    = "emqx/ESP32_R/sub"
topic_pub    = "emqx/ESP32_R/pub"
topic_button = "emqx/ESP32_R/arduino/button"
topic_led    = "emqx/ESP32_R/roboDK/led"

# ------- VBLES GLOBALES --------------------------
incremento = 300

# ------- STRUCTS ---------------------------------
@dataclass
class info_pedido:
    rgb_hex: str
    tamano: int
    cantidad: int

# ------- FUNCIONES DESEREALIZACION JSON ----------

class Payload(object):
    def __init__(self, rgb_hex, tamano, cantidad, tipo):
        self.rgb_hex = rgb_hex
        self.tamano = tamano
        self.cantidad = cantidad
        self.tipo = tipo

def as_payload(dct):
    return Payload(dct['rgb_hex'], dct['tamano'], dct['cantidad'], dct['tipo'])

# ------- FUNCION DE HANDLE ------------------------

def handle_message(mqttc, topic, payload):

    RDK = Robolink()

    # Conexión con la app
    if topic == topic_sub:
        desJson = json.loads(payload, object_hook = as_payload)
        message_to_pub = f"Cod: {desJson.rgb_hex}, Sz: {desJson.tamano}, q: {desJson.cantidad}, type: {desJson. tipo}"
        mqttc.publish(topic_pub, message_to_pub)

        # Meto en la cola la info del pedido
        if desJson.tipo == "Int":
            Init.cola_info_pedido_interior.put(info_pedido(desJson.rgb_hex, desJson.tamano, desJson.cantidad))

        else:
            Init.cola_info_pedido_exterior.put(info_pedido(desJson.rgb_hex, desJson.tamano, desJson.cantidad))

    # Conexión con la ESP32
    if topic == topic_button:
        # Si se ha pulsado el boton se hace la parada de emergencia
        if payload == "STOP":
            mqttc.publish(topic_led, "GREEN")
            RDK.setSimulationSpeed(0)

        # Si se vuelve a pulsar el proceso puede continuar
        else:
            mqttc.publish(topic_led, "RED")
            RDK.setSimulationSpeed(1)
