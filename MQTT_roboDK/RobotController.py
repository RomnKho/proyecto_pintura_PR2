# Script que handlea todo lo recibido por mqtt

import json
from queue import Queue
from robodk.robolink import *   # RoboDK API
from robodk.robomath import *   # Robot toolbox
from dataclasses import dataclass
import Init
import PickPlace
import Replace

topic_sub    = "emqx/ESP32_R/sub"
topic_pub    = "emqx/ESP32_R/pub"
topic_button = "emqx/ESP32_R/arduino/button"
topic_led    = "emqx/ESP32_R/roboDK/led"

# ------- VBLES GLOBALES --------------------------
RDK = Robolink()
incremento = 300

# ------- STRUCTS ---------------------------------
@dataclass
class info_pedido:
    rgb_hex: str
    tamano: str
    cantidad: int

@dataclass
class info_for_scara:
    tamano: str
    cantidad: int
    tipo: str

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

def handle_message(client, topic, payload):

    # Conexión con la app
    if topic == topic_sub:
        desJson_pedido = json.loads(payload, object_hook = as_payload_pedido)
        message_to_pub = f"Cod: {desJson_pedido.rgb_hex}, Sz: {desJson_pedido.tamano}, q: {desJson_pedido.cantidad}, type: {desJson_pedido. tipo}"
        client.publish(topic_pub, message_to_pub)

        # Meto en la cola la info del pedido
        if desJson_pedido.tipo == "Int":
            Init.cola_info_pedido_interior.put(info_pedido(desJson_pedido.rgb_hex, desJson_pedido.tamano, desJson_pedido.cantidad))
            with Init.mutex_pedido_interior:
                Init.botes_int_restantes += desJson_pedido.cantidad

            Init.cola_info_pedido_interior_tapas.put(info_pedido(desJson_pedido.rgb_hex, desJson_pedido.tamano, desJson_pedido.cantidad))
            with Init.mutex_pedido_tapas:
                Init.tapas_restantes += desJson_pedido.cantidad

        else:
            Init.cola_info_pedido_exterior.put(info_pedido(desJson_pedido.rgb_hex, desJson_pedido.tamano, desJson_pedido.cantidad))
            with Init.mutex_pedido_exterior:
                Init.botes_ext_restantes += desJson_pedido.cantidad
        
            Init.cola_info_pedido_exterior_tapas.put(info_pedido(desJson_pedido.rgb_hex, desJson_pedido.tamano, desJson_pedido.cantidad))
            with Init.mutex_pedido_tapas:
                Init.tapas_restantes += desJson_pedido.cantidad

    # Conexión con la ESP32
    if topic == topic_button:
        desJson_button =  json.loads(payload, object_hook = as_payload_button)
        message_to_pub = f"sensor: {desJson_button.sensor}, estado: {desJson_button.estado}"
        client.publish(topic_pub, message_to_pub)

        # Si se ha pulsado el boton se hace la parada de emergencia
        if desJson_button.estado == "STOP":
            msg_led = json.dumps({"actuador":"LED","color":"GREEN"})
            client.publish(topic_led, msg_led)
            RDK.setSimulationSpeed(0)

        # Si se vuelve a pulsar el proceso puede continuar
        else:
            msg_led = json.dumps({"actuador":"LED","color":"RED"})
            client.publish(topic_led, msg_led)
            RDK.setSimulationSpeed(1)

# ------- FUNCIONES DE PICK & PLACE ----------------

def move_scara():

    while True:
        # El SCARA espera a que haya una tapa física generada en la cinta
        datos_tapa = Init.cola_scara.get()
        tapa_obj = datos_tapa["item"]
        linea = datos_tapa["linea"]
        tam = datos_tapa["tam"]
        num_tapa = datos_tapa["num_tapa"]

        # Ir a por la tapa
        PickPlace.scara_pick(tapa_obj)
        # Le dice a la cinta que se puede seguir moviendo
        Init.stop_tapas = False
        # Decidir dónde ponerla según el tipo de pintura
        if linea == "Int":

            Init.cola_sinc_scara_interior.wait()
            Init.cola_sinc_scara_interior.clear()
            # Recojo el numero de bote a reemplazar
            num_bote = Init.cola_num_bote_int.get()
            
            PickPlace.scara_place_interior(tapa_obj, tam)
            Replace.reemplazo(linea, tam, num_bote, num_tapa)

            Init.stop_interior = False

        else:

            Init.cola_sinc_scara_exterior.wait()
            Init.cola_sinc_scara_exterior.clear()
            num_bote = Init.cola_num_bote_ext.get()

            PickPlace.scara_place_exterior(tapa_obj, tam)
            Replace.reemplazo(linea, tam, num_bote, num_tapa)

            Init.stop_exterior = False
