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

class payload_pedido(object):
    def __init__(self, rgb_hex, tamano, cantidad, tipo):
        self.rgb_hex = rgb_hex
        self.tamano = tamano
        self.cantidad = cantidad
        self.tipo = tipo

class payload_button(object):
    def __init__(self, sensor, estado):
        self.sensor = sensor
        self.estado = estado

def as_payload_pedido(dct):
    return payload_pedido(dct['rgb_hex'], dct['tamano'], dct['cantidad'], dct['tipo'])

def as_payload_button(dct):
    return payload_button(dct['sensor'], dct['estado'])

# ------- FUNCION DE HANDLE ------------------------

def handle_message(mqttc, topic, payload):

    RDK = Robolink()

    # Conexión con la app
    if topic == topic_sub:
        desJson_pedido = json.loads(payload, object_hook = as_payload_pedido)
        message_to_pub = f"Cod: {desJson_pedido.rgb_hex}, Sz: {desJson_pedido.tamano}, q: {desJson_pedido.cantidad}, type: {desJson_pedido. tipo}"
        mqttc.publish(topic_pub, message_to_pub)

        # Meto en la cola la info del pedido
        if desJson_pedido.tipo == "Int":
            Init.cola_info_pedido_interior.put(info_pedido(desJson_pedido.rgb_hex, desJson_pedido.tamano, desJson_pedido.cantidad))

        else:
            Init.cola_info_pedido_exterior.put(info_pedido(desJson_pedido.rgb_hex, desJson_pedido.tamano, desJson_pedido.cantidad))

    # Conexión con la ESP32
    if topic == topic_button:
        desJson_button =  json.loads(payload, object_hook = as_payload_button)
        message_to_pub = f"sensor: {desJson_button.sensor}, estado: {desJson_button.estado}"
        mqttc.publish(topic_pub, message_to_pub)

        # Si se ha pulsado el boton se hace la parada de emergencia
        if desJson_button.estado == "STOP":
            msg_led = json.dumps({"actuador":"LED","color":"GREEN"})
            mqttc.publish(topic_led, msg_led)
            RDK.setSimulationSpeed(0)

        # Si se vuelve a pulsar el proceso puede continuar
        else:
            msg_led = json.dumps({"actuador":"LED","color":"RED"})
            mqttc.publish(topic_led, msg_led)
            RDK.setSimulationSpeed(1)
