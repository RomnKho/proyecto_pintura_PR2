# Type help("robodk.robolink") or help("robodk.robomath") for more information
# Press F5 to run the script
# Documentation: https://robodk.com/doc/en/RoboDK-API.html
# Reference:     https://robodk.com/doc/en/PythonAPI/robodk.html
# Note: It is not required to keep a copy of this file, your Python script is saved with your RDK project

# You can also use the new version of the API:
from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox
RDK = robolink.Robolink()

import init

import threading
import time

def sensor_final_ext_collision():
    colision = False
    colision_prev = False
    sensor = RDK.Item('Sensor_Final_Ext', robolink.ITEM_TYPE_SENSOR)
    objeto = RDK.Item('CBote_Ext', robolink.ITEM_TYPE_OBJECT)
    if sensor.Collisions(objeto):
        colision = True
    if colision and not colision_prev:
        init.bote_procesado_ext.set()  # Indicar que el bote externo ha terminado
        init.bote_listo_robot_ext.set()  # Indicar que el bote externo está listo para el robot
    colision_prev = colision
    time.sleep(0.1)

def sensor_final_int_collision():
    colision = False
    colision_prev = False
    sensor = RDK.Item('Sensor_Final_Int', robolink.ITEM_TYPE_SENSOR)
    objeto = RDK.Item('CBote_Int', robolink.ITEM_TYPE_OBJECT)
    if sensor.Collisions(objeto):
        colision = True
    if colision and not colision_prev:
        init.bote_procesado_int.set()  # Indicar que el bote interno ha terminado
        init.bote_listo_robot_int.set()  # Indicar que el bote interno está listo para el robot
    colision_prev = colision
    time.sleep(0.1)

threading.Thread(target=sensor_final_ext_collision).start()
threading.Thread(target=sensor_final_int_collision).start()

