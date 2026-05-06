# Script de python para MQTT

import threading
import time
from robodk.robomath import *
from robodk.robolink import *
import paho.mqtt.client as mqtt
import RobotController  as rc
import Init
import MoveCinta as mc

broker_dsic  = "mqtt.dsic.upv.es"
free_broker  = "broker.emqx.io"
port         = 1883
user_dsic    = "giirob"
passwd_dsic  = "UPV2024"
topic_sub    = "emqx/ESP32_R/sub"
topic_pub    = "emqx/ESP32_R/pub"
topic_button = "emqx/ESP32_R/arduino/button"

RDK = Robolink()

# Callback
def on_message(mqttc, obj, msg): 
    payload = msg.payload.decode('utf-8')
    topic = msg.topic
    qos = msg.qos
    mqttc.publish(topic_pub, "Estoy en on_message")
    rc.handle_message(mqttc, topic, payload)

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_message = on_message

# mqttc.username_pw_set(username=user, password=passwd)
mqttc.connect(free_broker, port, 60)
mqttc.subscribe(topic_sub, 0)
mqttc.subscribe(topic_button, 0)

# Crear los threads
hilo_cintas = threading.Thread(target = mc.mueve_cinta)
hilo_generar_botes_interior = threading.Thread(target = mc.generar_bote_interior)
hilo_generar_botes_exterior = threading.Thread(target = mc.generar_bote_exterior)
hilo_pintar_botes = threading.Thread(target = mc.pintar_bote_interior)

# Hacer que empiecen los threads
hilo_cintas.start()
hilo_generar_botes_interior.start()
hilo_generar_botes_exterior.start()
hilo_pintar_botes.start()

mqttc.publish(topic_pub, "Ready from RoboDK")

mqttc.loop_forever()