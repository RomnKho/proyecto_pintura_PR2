# Script de python para MQTT

import threading
import time
from robodk.robomath import *
from robodk.robolink import *
import paho.mqtt.client as mqtt
import RobotController  as rc
import mqtt_client as mqtt
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
def on_message(client, userdata, msg): 
    payload = msg.payload.decode('utf-8')
    topic = msg.topic
    qos = msg.qos
    
    rc.handle_message(client, topic, payload)

mqtt.manager.connect()  # Se conecta al broker 
mqtt.manager.start()    # Hace empezar el loop no bloqueante

mqtt.manager.subscribe(topic_sub, on_message)
mqtt.manager.subscribe(topic_button, on_message)

mqtt.manager.publish(topic_pub, "Ready from RoboDK")

# Crear los threads
hilo_cinta_interior = threading.Thread(target = mc.mueve_cinta_interior)
hilo_cinta_exterior = threading.Thread(target = mc.mueve_cinta_exterior)
hilo_cinta_tapas = threading.Thread(target = mc.mueve_cinta_tapas)
hilo_generar_botes_interior = threading.Thread(target = mc.generar_bote_interior)
hilo_generar_botes_exterior = threading.Thread(target = mc.generar_bote_exterior)
hilo_generar_tapas = threading.Thread(target = mc.generar_tapas)
hilo_pintar_bote_interior = threading.Thread(target = mc.pintar_bote_interior)
hilo_pintar_bote_exterior = threading.Thread(target = mc.pintar_bote_exterior)
hilo_scara = threading.Thread(target = rc.move_scara)

# Hacer que empiecen los threads
hilo_cinta_interior.start()
hilo_cinta_exterior.start()
hilo_cinta_tapas.start()
hilo_generar_botes_interior.start()
hilo_generar_botes_exterior.start()
hilo_generar_tapas.start()
hilo_pintar_bote_interior.start()
hilo_pintar_bote_exterior.start()
hilo_scara.start()
