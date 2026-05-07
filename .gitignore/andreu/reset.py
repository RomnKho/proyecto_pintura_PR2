# Type help("robodk.robolink") or help("robodk.robomath") for more information
# Press F5 to run the script
# Documentation: https://robodk.com/doc/en/RoboDK-API.html
# Reference:     https://robodk.com/doc/en/PythonAPI/robodk.html
# Note: It is not required to keep a copy of this file, your Python script is saved with your RDK project

# You can also use the new version of the API:
from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox

import init
import time
RDK = robolink.Robolink()

def reset():

    init.running = False
    time.sleep(1) # Esperamos a que los hilos terminen su ejecución

    init.clean_init()

    objetos_estacion = RDK.ItemList(robolink.ITEM_TYPE_OBJECT)
    for obj in objetos_estacion:
        if obj.Name().startswith("CBote") or obj.Name().startswith("CTapa"):
            obj.Delete()
        elif "Bote_" in obj.Name() or "Tapa_" in obj.Name():
            obj.setVisible(False)

    robots = RDK.ItemList(robolink.ITEM_TYPE_ROBOT)
    for robot in robots:
        pose_inicial = [0.0] * len(robot.Joints().list())
        robot.setJoints(pose_inicial)
        # robot.MoveJ(pose_inicial, blocking=False)

    ... # Aquí podríamos agregar cualquier otra limpieza o reinicio necesario para el estado del sistema

if __name__ == "__main__":
    reset()