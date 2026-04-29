# Script que handlea todo lo recibido por mqtt

from robodk.robolink import *   # RoboDK API
from robodk.robomath import *   # Robot toolbox

RDK = Robolink()

def handle_message(mqttc, topic, payload):

    if topic == "emqtx/ESP32_R/sub":
        move_robot(payload)

# [TEST] Mueve el Scara
def move_robot(position):
    robot       = RDK.Item("Scara", ITEM_TYPE_ROBOT)
    PrePick     = RDK.Item("[TAPAS] PrePick", ITEM_TYPE_TARGET)
    Pick        = RDK.Item("[TAPAS] Pick", ITEM_TYPE_TARGET)
    PostPick    = RDK.Item("[TAPAS] PostPick", ITEM_TYPE_TARGET)

    if robot.Valid() and PrePick.Valid() and Pick.Valid() and PostPick.Valid():
        robot.MoveJ(PrePick)
        robot.MoveL(Pick)
        robot.MoveL(PostPick)


    


