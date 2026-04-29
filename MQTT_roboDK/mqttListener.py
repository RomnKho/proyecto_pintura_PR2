# Script de python para MQTT

import json
import paho.mqtt.client as mqtt
import RobotController  as rc


broker_dsic = "mqtt.dsic.upv.es"
free_broker = "broker.emqx.io"
port        = 1883
user_dsic   = "giirob"
passwd_dsic = "UPV2024"
topic_sub   = "emqx/ESP32_R/sub"
topic_pub   = "emqx/ESP32_R/pub"

# Source - https://stackoverflow.com/a/16826012
# Posted by Alex
# Retrieved 2026-04-27, License - CC BY-SA 3.0

class Payload(object):
    def __init__(self, rgb_hex, tamano, cantidad, tipo):
        self.rgb_hex = rgb_hex
        self.tamano = tamano
        self.cantidad = cantidad
        self.tipo = tipo

def as_payload(dct):
    return Payload(dct['rgb_hex'], dct['tamano'], dct['cantidad'], dct['tipo'])
# Callback
def on_message(mqttc, obj, msg):
    payload = msg.payload.decode('utf-8')
    topic = msg.topic
    qos = msg.qos
    desJson = json.loads(payload, object_hook = as_payload)
    message_to_pub = f"Cod: {desJson.rgb_hex}, Sz: {desJson.tamano}, q: {desJson.cantidad}, type: {desJson. tipo}"
    mqttc.publish(topic_pub, message_to_pub)
    rc.handle_message(mqttc, topic, payload) # for the movement of the robot


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_message = on_message

# mqttc.username_pw_set(username=user, password=passwd)
mqttc.connect(free_broker, port, 60)
mqttc.subscribe(topic_sub, 0)

mqttc.publish(topic_pub, "Ready from RoboDK")

mqttc.loop_forever()