# mqttListener.py

import json
import pintproyecto.mqtt_client as mqtt
import pintproyecto.procesos as p

from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox

RDK = robolink.Robolink()

TOPIC_SUB           = "emqx/ESP32_R/sub"
TOPIC_BUTTON_SUB    = "emqx/ESP32_R/arduino/button"

TOPIC_PUB           = "emqx/ESP32_R/pub/global"
TOPIC_LED_PUB       = "emqx/ESP32_R/roboDK/led"
TOPIC_ULTRA_PUB     = "emqx/ESP32_R/arduino/ultrasonico"


def normalizar_payload(data):
    # Cantidad
    data["cantidad"] = int(data.get("cantidad", 1))

    # Tipo
    #Permitimos "int", "interior", "ext", "exterior"
    tipo = data.get("tipo", "interior").lower()
    if tipo in ["int", "interior"]:
        data["tipo"] = "interior"
    elif tipo in ["ext", "exterior"]:
        data["tipo"] = "exterior"
    else:        
        data["tipo"] = "interior"

    # Tamaño
    tamano = str(data.get("tamano", data.get("tam", "2L")))

    # Por si desde la ESP32 mandas G/M/P
    mapa_tamanos = {
        "G": "5L",
        "M": "2L",
        "P": "0.5L",
        "g": "5L",
        "m": "2L",
        "p": "0.5L",
        "grande": "5L",
        "mediano": "2L",
        "pequeno": "0.5L",
        "pequeño": "0.5L",
    }

    tamano = mapa_tamanos.get(tamano, tamano)

    if tamano not in ["5L", "2L", "0.5L"]:
        tamano = "2L"

    data["tamano"] = tamano
    data["tam"] = tamano

    # Color
    if "rgb_hex" in data:
        data["color"] = data["rgb_hex"]

    elif "color" not in data:
        data["color"] = "#FFFFFF"

    return data


def on_message(client, userdata, msg):
    try:
        payload_txt = msg.payload.decode("utf-8")
        topic = msg.topic

        print(f"[MQTT] Mensaje recibido en {topic}: {payload_txt}")

        if topic == TOPIC_SUB:
            data = json.loads(payload_txt)
            data = normalizar_payload(data)

            handle_message(client, topic, json.dumps(data))

            mqtt.manager.publish(
                TOPIC_PUB,
                f"Pedido recibido: {json.dumps(data)}"
            )
        else:
            handle_message(client, topic, payload_txt)

    except Exception as e:
        print(f"[MQTT] Error procesando mensaje: {e}")
        mqtt.manager.publish(TOPIC_PUB, f"Error procesando pedido: {e}")

def handle_message(client, topic, payload):
    try:
        if topic == TOPIC_SUB:
            p.handle_process(payload)

        elif topic == TOPIC_BUTTON_SUB:
            desJson_button = json.loads(payload)
            sensor = desJson_button.get("sensor", "desconocido")
            estado = desJson_button.get("estado", "")
            message_to_pub = f"sensor: {sensor}, estado: {estado}"
            client.publish(TOPIC_PUB, message_to_pub)

            if estado == "STOP":
                msg_led = json.dumps({"actuador": "LED", "color": "GREEN"})
                client.publish(TOPIC_LED_PUB, msg_led)
                RDK.setSimulationSpeed(0)
            else:
                msg_led = json.dumps({"actuador": "LED", "color": "RED"})
                client.publish(TOPIC_LED_PUB, msg_led)
                RDK.setSimulationSpeed(1.8)
                
        elif topic == TOPIC_ULTRA_PUB:
            desJson_ultra = json.loads(payload)
            distancia = desJson_ultra.get("distancia", "desconocida")
            message_to_pub = f"ultrasonico: {distancia} cm"
            client.publish(TOPIC_PUB, message_to_pub)

    except Exception as e:
        print(f"[MQTT] Error en handle_message: {e}")
        mqtt.manager.publish(TOPIC_PUB, f"Error procesando pedido: {e}") 


def iniciar_mqtt():
    mqtt.manager.subscribe(TOPIC_SUB, on_message)
    mqtt.manager.subscribe(TOPIC_BUTTON_SUB, on_message)
    mqtt.manager.subscribe(TOPIC_ULTRA_PUB, on_message)
    mqtt.manager.publish(TOPIC_PUB, "Ready from RoboDK")
    print("[MQTT] Listener iniciado")


# Si ejecutas este archivo directamente
if __name__ == "__main__":
    iniciar_mqtt()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        mqtt.manager.disconnect()