# Script de python para MQTT

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

# Callback
def on_message(mqttc, obj, msg):
    payload = msg.payload.decode('utf-8')
    topic = msg.topic
    qos = msg.qos
    rc.handle_message(mqttc, topic, payload) # for the movement of the robot


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_message = on_message

# mqttc.username_pw_set(username=user, password=passwd)
mqttc.connect(free_broker, port, 60)
mqttc.subscribe(topic_sub, 0)

mqttc.publish(topic_pub, "Ready from RoboDK")

mqttc.loop_forever()