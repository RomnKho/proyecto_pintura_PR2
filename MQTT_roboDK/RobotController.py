# Script que handlea todo lo recibido por mqtt

import json
from robodk.robolink import *   # RoboDK API
from robodk.robomath import *   # Robot toolbox
import MoveCinta 

RDK = Robolink()
topic_pub = "emqx/ESP32_R/pub"

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
    if topic == "emqx/ESP32_R/sub":
        desJson = json.loads(payload, object_hook = as_payload)
        message_to_pub = f"Cod: {desJson.rgb_hex}, Sz: {desJson.tamano}, q: {desJson.cantidad}, type: {desJson. tipo}"
        mqttc.publish(topic_pub, message_to_pub)
        MoveCinta.move_cinta(desJson.cantidad, desJson.rgb_hex)

# ------- FUNCIONES DE PICK & PLACE ----------------

# [TEST] Mueve el Scara
def move_robot(mqttc):
    robot       = RDK.Item("Scara", ITEM_TYPE_ROBOT)
    PrePick     = RDK.Item("[TAPAS] PrePick", ITEM_TYPE_TARGET)
    Pick        = RDK.Item("[TAPAS] Pick", ITEM_TYPE_TARGET)
    PostPick    = RDK.Item("[TAPAS] PostPick", ITEM_TYPE_TARGET)
    mqttc.publish(topic_pub, "He definido todos los items")
    
    if robot.Valid() and PrePick.Valid() and Pick.Valid() and PostPick.Valid():
        mqttc.publish(topic_pub, "He entrado al if antes de mover")
        robot.MoveJ(PrePick)
        robot.MoveJ(Pick)
        robot.MoveJ(PostPick)
        mqttc.publish(topic_pub, "He hecho los movimientos")

    

