# Type help("robodk.robolink") or help("robodk.robomath") for more information
# Press F5 to run the script
# Documentation: https://robodk.com/doc/en/RoboDK-API.html
# Reference:     https://robodk.com/doc/en/PythonAPI/robodk.html
# Note: It is not required to keep a copy of this file, your Python script is saved with your RDK project

# You can also use the new version of the API:
from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox

import time
import pintproyecto.init as init
from pintproyecto.init import TipoBote, Agitador
import pintproyecto.procesos as procesos

RDK_G = robolink.Robolink()
robot_ext = RDK_G.Item('[EXTERIOR]Yaskawa_Motoman', robolink.ITEM_TYPE_ROBOT)
robot_int = RDK_G.Item('[INTERIOR]Yaskawa_Motoman', robolink.ITEM_TYPE_ROBOT)

herramienta_pos_init = [0, 0, 0, 0, 0, 0]
herramienta_pos_abierta = [200, 0, 0, 0, 0, 0]
herramienta_pos_cerrada = [170, 0, 0, 0, 0, 0]

def move_j(robot, target):
    robot.MoveJ(target, blocking=False)
    time.sleep(0.2)

def move_l(robot, target):
    robot.MoveL(target, blocking=False)
    time.sleep(0.2)

def meter_bote(bote_con_tapa, linea, agitador):
    with init.agitadores_lock:
        if linea == TipoBote.INTERIOR:
            pickandplace_agitador_int(bote_con_tapa, agitador)
        else:
            pickandplace_agitador_ext(bote_con_tapa, agitador)

def sacar_bote(bote_con_tapa, linea, agitador):
    with init.agitadores_lock:
        if linea == TipoBote.INTERIOR:
            pick_and_place_pedestal_int(bote_con_tapa, agitador)
        else:
            pick_and_place_pedestal_ext(bote_con_tapa, agitador)


def pickandplace_agitador_int(bote_con_tapa, agitador):
    agitador_pick_int(robot_int, bote_con_tapa)
    time.sleep(0.5)
    if agitador == Agitador.DER_INT:
        place_agitador_der_int(robot_int, bote_con_tapa)
    else:
        place_agitador_izq_int(robot_int, bote_con_tapa)

def pickandplace_agitador_ext(bote_con_tapa, agitador):
    agitador_pick_ext(robot_ext, bote_con_tapa)
    time.sleep(0.5)
    if agitador == Agitador.DER_EXT:
        place_agitador_der_ext(robot_ext, bote_con_tapa)
    else:
        place_agitador_izq_ext(robot_ext, bote_con_tapa)

def pick_and_place_pedestal_int(bote_con_tapa, agitador):
    if agitador == Agitador.DER_INT:
        pick_agitador_der_int(robot_int, bote_con_tapa)
    else:
        pick_agitador_izq_int(robot_int, bote_con_tapa)
    time.sleep(0.5)
    place_pedestal_int(robot_int, bote_con_tapa)

def pick_and_place_pedestal_ext(bote_con_tapa, agitador):
    if agitador == Agitador.DER_EXT:
        pick_agitador_der_ext(robot_ext, bote_con_tapa)
    else:
        pick_agitador_izq_ext(robot_ext, bote_con_tapa)
    time.sleep(0.5)
    place_pedestal_ext(robot_ext, bote_con_tapa)

def agitador_pick_int(robot, bote_con_tapa):
    RDK = robolink.Robolink()
    herramienta_pos = RDK.Item("[INTERIOR]PinzaCobot", robolink.ITEM_TYPE_ROBOT)
    reposo_pos = RDK.Item("[INTERIOR]Reposo", robolink.ITEM_TYPE_TARGET)
    punto_paso_pos = RDK.Item("[INTERIOR]PuntoPaso", robolink.ITEM_TYPE_TARGET)
    base_frame_pos = RDK.Item("[INTERIOR]Pick&PlaceAgitador", robolink.ITEM_TYPE_FRAME)
    prepick_pos = RDK.Item("[INTERIOR]PrePick", robolink.ITEM_TYPE_TARGET)
    pick_pos = RDK.Item("[INTERIOR]Pick", robolink.ITEM_TYPE_TARGET)
    post_pick_pos = prepick_pos

    if not (reposo_pos.Valid() and punto_paso_pos.Valid() and base_frame_pos.Valid() and prepick_pos.Valid() and pick_pos.Valid() and post_pick_pos.Valid()):
        RDK.ShowMessage("Alguno de los targets no es válido en agitador_pick_int")
        return
    
    robot.setPoseFrame(base_frame_pos)
    move_j(robot, reposo_pos)
    move_j(robot, punto_paso_pos)
    move_j(robot, prepick_pos)
    herramienta_pos.MoveJ(herramienta_pos_abierta)  # Abrir pinza
    move_l(robot, pick_pos)
    time.sleep(0.2)
    herramienta_pos.MoveJ(herramienta_pos_cerrada)  # Cerrar pinza
    bote_con_tapa.rdk_item.setParentStatic(herramienta_pos)
    time.sleep(0.5)
    move_l(robot, prepick_pos)
    move_j(robot, punto_paso_pos)
                        
def agitador_pick_ext(robot, bote_con_tapa):
    RDK = robolink.Robolink()
    herramienta_pos = RDK.Item("[EXTERIOR]PinzaCobot", robolink.ITEM_TYPE_ROBOT)
    reposo_pos = RDK.Item("[EXTERIOR]Reposo", robolink.ITEM_TYPE_TARGET)
    punto_paso_pos = RDK.Item("[EXTERIOR]PuntoPaso", robolink.ITEM_TYPE_TARGET)
    base_frame_pos = RDK.Item("[EXTERIOR]Pick&PlaceAgitador", robolink.ITEM_TYPE_FRAME)
    prepick_pos = RDK.Item("[EXTERIOR]PrePick", robolink.ITEM_TYPE_TARGET)
    pick_pos = RDK.Item("[EXTERIOR]Pick", robolink.ITEM_TYPE_TARGET)
    post_pick_pos = prepick_pos

    if not (reposo_pos.Valid() and punto_paso_pos.Valid() and base_frame_pos.Valid() and prepick_pos.Valid() and pick_pos.Valid() and post_pick_pos.Valid() and herramienta_pos.Valid()):
        RDK.ShowMessage("Alguno de los targets no es válido en agitador_pick_ext")
        return

    robot.setPoseFrame(base_frame_pos)
    move_j(robot, reposo_pos)
    move_j(robot, punto_paso_pos)
    move_j(robot, prepick_pos)
    herramienta_pos.MoveJ(herramienta_pos_abierta)  # Abrir pinza
    move_l(robot, pick_pos)
    time.sleep(0.5)
    herramienta_pos.MoveJ(herramienta_pos_cerrada)  # Cerrar pinza
    bote_con_tapa.rdk_item.setParentStatic(herramienta_pos)
    time.sleep(0.5)
    move_l(robot, prepick_pos)
    move_j(robot, punto_paso_pos)

def place_agitador_der_int(robot, bote_con_tapa):
    RDK = robolink.Robolink()
    reposo_pos = RDK.Item("[INTERIOR]Reposo", robolink.ITEM_TYPE_TARGET)
    punto_paso_pos = RDK.Item("[INTERIOR]PuntoPaso", robolink.ITEM_TYPE_TARGET)
    base_frame_pos = RDK.Item("[INTERIOR]Pick&PlaceAgitador", robolink.ITEM_TYPE_FRAME)
    preplace_der_pos = RDK.Item("[INTERIOR]PrePlaceAgitadoraDerecha", robolink.ITEM_TYPE_TARGET)
    place_der_pos = RDK.Item("[INTERIOR]PlaceAgitadoraDerecha", robolink.ITEM_TYPE_TARGET)
    post_place_der_pos = preplace_der_pos
    agitador_obj = RDK.Item("[INTERIOR]PedestalDerecha", robolink.ITEM_TYPE_FRAME)
    herramienta_pos = RDK.Item("[INTERIOR]PinzaCobot", robolink.ITEM_TYPE_ROBOT)

    if not (reposo_pos.Valid() and punto_paso_pos.Valid() and base_frame_pos.Valid() and preplace_der_pos.Valid() and place_der_pos.Valid() and post_place_der_pos.Valid() and agitador_obj.Valid()):
        RDK.ShowMessage("Alguno de los targets no es válido en place_agitador_der_int")
        return
    
    robot.setPoseFrame(base_frame_pos)
    move_j(robot, punto_paso_pos)
    move_j(robot, preplace_der_pos)
    move_l(robot, place_der_pos)
    time.sleep(0.5)
    bote_con_tapa.rdk_item.setParentStatic(agitador_obj)
    herramienta_pos.MoveJ(herramienta_pos_abierta)  # Abrir pinza
    time.sleep(0.5)
    move_l(robot, post_place_der_pos)
    herramienta_pos.MoveJ(herramienta_pos_cerrada)  # Cerrar pinza
    move_j(robot, punto_paso_pos)
    move_j(robot, reposo_pos)
                            
def place_agitador_izq_int(robot, bote_con_tapa):
    RDK = robolink.Robolink()
    reposo_pos = RDK.Item("[INTERIOR]Reposo", robolink.ITEM_TYPE_TARGET)
    punto_paso_pos = RDK.Item("[INTERIOR]PuntoPaso", robolink.ITEM_TYPE_TARGET)
    base_frame_pos = RDK.Item("[INTERIOR]Pick&PlaceAgitador", robolink.ITEM_TYPE_FRAME)
    preplace_izq_pos = RDK.Item("[INTERIOR]PrePlaceAgitadoraIzquierda", robolink.ITEM_TYPE_TARGET)
    place_izq_pos = RDK.Item("[INTERIOR]PlaceAgitadoraIzquierda", robolink.ITEM_TYPE_TARGET)
    post_place_izq_pos = preplace_izq_pos
    agitador_obj = RDK.Item("[INTERIOR]PedestalIzquierda", robolink.ITEM_TYPE_FRAME)
    herramienta_pos = RDK.Item("[INTERIOR]PinzaCobot", robolink.ITEM_TYPE_ROBOT)

    if not (reposo_pos.Valid() and punto_paso_pos.Valid() and base_frame_pos.Valid() and preplace_izq_pos.Valid() and place_izq_pos.Valid() and post_place_izq_pos.Valid() and agitador_obj.Valid()):
        RDK.ShowMessage("Alguno de los targets no es válido en place_agitador_izq_int")
        return
    
    robot.setPoseFrame(base_frame_pos)

    move_j(robot, punto_paso_pos)
    move_j(robot, preplace_izq_pos)
    move_l(robot, place_izq_pos)
    time.sleep(0.5)
    bote_con_tapa.rdk_item.setParentStatic(agitador_obj)
    herramienta_pos.MoveJ(herramienta_pos_abierta)  # Abrir pinza
    time.sleep(0.5)
    move_l(robot, post_place_izq_pos)
    herramienta_pos.MoveJ(herramienta_pos_cerrada)  # Cerrar pinza
    move_j(robot, punto_paso_pos)
    move_j(robot, reposo_pos)

def place_agitador_der_ext(robot, bote_con_tapa):
    RDK = robolink.Robolink()
    reposo_pos = RDK.Item("[EXTERIOR]Reposo", robolink.ITEM_TYPE_TARGET)
    punto_paso_pos = RDK.Item("[EXTERIOR]PuntoPaso", robolink.ITEM_TYPE_TARGET)
    base_frame_pos = RDK.Item("[EXTERIOR]Pick&PlaceAgitador", robolink.ITEM_TYPE_FRAME)
    preplace_der_pos = RDK.Item("[EXTERIOR]PrePlaceAgitadoraDerecha", robolink.ITEM_TYPE_TARGET)
    place_der_pos = RDK.Item("[EXTERIOR]PlaceAgitadoraDerecha", robolink.ITEM_TYPE_TARGET)
    post_place_der_pos = preplace_der_pos
    agitador_obj = RDK.Item("[EXTERIOR]PedestalDerecha", robolink.ITEM_TYPE_FRAME)
    herramienta_pos = RDK.Item("[EXTERIOR]PinzaCobot", robolink.ITEM_TYPE_ROBOT)

    if not (reposo_pos.Valid() and punto_paso_pos.Valid() and base_frame_pos.Valid() and preplace_der_pos.Valid() and place_der_pos.Valid() and post_place_der_pos.Valid() and agitador_obj.Valid()):
        RDK.ShowMessage("Alguno de los targets no es válido en place_agitador_der_ext")
        return
    
    robot.setPoseFrame(base_frame_pos)

    move_j(robot, punto_paso_pos)
    move_j(robot, preplace_der_pos)
    move_l(robot, place_der_pos)
    time.sleep(0.5)
    bote_con_tapa.rdk_item.setParentStatic(agitador_obj)
    herramienta_pos.MoveJ(herramienta_pos_abierta)  # Abrir pinza
    time.sleep(0.5)
    move_l(robot, post_place_der_pos)
    herramienta_pos.MoveJ(herramienta_pos_cerrada)  # Cerrar pinza
    move_j(robot, punto_paso_pos)
    move_j(robot, reposo_pos)
    
def place_agitador_izq_ext(robot, bote_con_tapa):
    RDK = robolink.Robolink()
    reposo_pos = RDK.Item("[EXTERIOR]Reposo", robolink.ITEM_TYPE_TARGET)
    punto_paso_pos = RDK.Item("[EXTERIOR]PuntoPaso", robolink.ITEM_TYPE_TARGET)
    base_frame_pos = RDK.Item("[EXTERIOR]Pick&PlaceAgitador", robolink.ITEM_TYPE_FRAME)
    preplace_izq_pos = RDK.Item("[EXTERIOR]PrePlaceAgitadoraIzquierda", robolink.ITEM_TYPE_TARGET)
    place_izq_pos = RDK.Item("[EXTERIOR]PlaceAgitadoraIzquierda", robolink.ITEM_TYPE_TARGET)
    post_place_izq_pos = preplace_izq_pos
    agitador_obj = RDK.Item("[EXTERIOR]PedestalIzquierda", robolink.ITEM_TYPE_FRAME)
    herramienta_pos = RDK.Item("[EXTERIOR]PinzaCobot", robolink.ITEM_TYPE_ROBOT)

    if not (reposo_pos.Valid() and punto_paso_pos.Valid() and base_frame_pos.Valid() and preplace_izq_pos.Valid() and place_izq_pos.Valid() and post_place_izq_pos.Valid() and agitador_obj.Valid()):
        RDK.ShowMessage("Alguno de los targets no es válido en place_agitador_izq_ext")
        return
    
    robot.setPoseFrame(base_frame_pos)

    move_j(robot, punto_paso_pos)
    move_j(robot, preplace_izq_pos)
    move_l(robot, place_izq_pos)
    time.sleep(0.5)
    bote_con_tapa.rdk_item.setParentStatic(agitador_obj)
    herramienta_pos.MoveJ(herramienta_pos_abierta)  # Abrir pinza
    time.sleep(0.5)
    move_l(robot, post_place_izq_pos)
    herramienta_pos.MoveJ(herramienta_pos_cerrada)  # Cerrar pinza
    move_j(robot, punto_paso_pos)
    move_j(robot, reposo_pos)


# ----
# ----
# ----

def pick_agitador_der_int(robot, bote_con_tapa):
    RDK = robolink.Robolink()
    reposo_pos = RDK.Item("[INTERIOR]Reposo", robolink.ITEM_TYPE_TARGET)
    punto_paso_pos = RDK.Item("[INTERIOR]PuntoPaso", robolink.ITEM_TYPE_TARGET)
    base_frame_pos = RDK.Item("[INTERIOR]Pick&PlaceAgitador", robolink.ITEM_TYPE_FRAME)
    prepick_der_pos = RDK.Item("[INTERIOR]PrePlaceAgitadoraDerecha", robolink.ITEM_TYPE_TARGET)
    pick_der_pos = RDK.Item("[INTERIOR]PlaceAgitadoraDerecha", robolink.ITEM_TYPE_TARGET)
    post_pick_der_pos = prepick_der_pos
    herramienta_pos = RDK.Item("[INTERIOR]PinzaCobot", robolink.ITEM_TYPE_ROBOT)

    if not (reposo_pos.Valid() and punto_paso_pos.Valid() and base_frame_pos.Valid() and prepick_der_pos.Valid() and pick_der_pos.Valid() and post_pick_der_pos.Valid() and herramienta_pos.Valid()):
        RDK.ShowMessage("Alguno de los targets no es válido en pick_agitador_der_int")
        return

    robot.setPoseFrame(base_frame_pos)

    move_j(robot, reposo_pos)
    move_j(robot, punto_paso_pos)
    move_j(robot, prepick_der_pos)
    herramienta_pos.MoveJ(herramienta_pos_cerrada)  # Abrir pinza
    move_l(robot, pick_der_pos)
    time.sleep(0.5)
    herramienta_pos.MoveJ(herramienta_pos_cerrada)  # Cerrar pinza
    bote_con_tapa.rdk_item.setParentStatic(herramienta_pos)
    time.sleep(0.5)
    move_l(robot, post_pick_der_pos)
    move_j(robot, punto_paso_pos)

def pick_agitador_izq_int(robot, bote_con_tapa):
    RDK = robolink.Robolink()
    reposo_pos = RDK.Item("[INTERIOR]Reposo", robolink.ITEM_TYPE_TARGET)
    punto_paso_pos = RDK.Item("[INTERIOR]PuntoPaso", robolink.ITEM_TYPE_TARGET)
    base_frame_pos = RDK.Item("[INTERIOR]Pick&PlaceAgitador", robolink.ITEM_TYPE_FRAME)
    prepick_izq_pos = RDK.Item("[INTERIOR]PrePlaceAgitadoraIzquierda", robolink.ITEM_TYPE_TARGET)
    pick_izq_pos = RDK.Item("[INTERIOR]PlaceAgitadoraIzquierda", robolink.ITEM_TYPE_TARGET)
    post_pick_izq_pos = prepick_izq_pos
    herramienta_pos = RDK.Item("[INTERIOR]PinzaCobot", robolink.ITEM_TYPE_ROBOT)

    if not (reposo_pos.Valid() and punto_paso_pos.Valid() and prepick_izq_pos.Valid() and pick_izq_pos.Valid() and post_pick_izq_pos.Valid() and herramienta_pos.Valid() and base_frame_pos.Valid()):
        RDK.ShowMessage("Alguno de los targets no es válido en pick_agitador_izq_int")
        return
    
    robot.setPoseFrame(base_frame_pos)

    move_j(robot, reposo_pos)
    move_j(robot, punto_paso_pos)
    move_j(robot, prepick_izq_pos)
    herramienta_pos.MoveJ(herramienta_pos_abierta)  # Abrir pinza
    move_l(robot, pick_izq_pos)
    time.sleep(0.5)
    bote_con_tapa.rdk_item.setParentStatic(herramienta_pos)
    herramienta_pos.MoveJ(herramienta_pos_cerrada)  # Cerrar pinza
    time.sleep(0.5)
    move_l(robot, post_pick_izq_pos)
    move_j(robot, punto_paso_pos)

def pick_agitador_der_ext(robot, bote_con_tapa):
    RDK = robolink.Robolink()
    reposo_pos = RDK.Item("[EXTERIOR]Reposo", robolink.ITEM_TYPE_TARGET)
    punto_paso_pos = RDK.Item("[EXTERIOR]PuntoPaso", robolink.ITEM_TYPE_TARGET)
    base_frame_pos = RDK.Item("[EXTERIOR]Pick&PlaceAgitador", robolink.ITEM_TYPE_FRAME)
    prepick_der_pos = RDK.Item("[EXTERIOR]PrePlaceAgitadoraDerecha", robolink.ITEM_TYPE_TARGET)
    pick_der_pos = RDK.Item("[EXTERIOR]PlaceAgitadoraDerecha", robolink.ITEM_TYPE_TARGET)
    post_pick_der_pos = prepick_der_pos
    herramienta_pos = RDK.Item("[EXTERIOR]PinzaCobot", robolink.ITEM_TYPE_ROBOT)

    if not (reposo_pos.Valid() and punto_paso_pos.Valid() and prepick_der_pos.Valid() and pick_der_pos.Valid() and post_pick_der_pos.Valid() and herramienta_pos.Valid() and base_frame_pos.Valid()):
        RDK.ShowMessage("Alguno de los targets no es válido en pick_agitador_der_ext")
        return

    robot.setPoseFrame(base_frame_pos)

    move_j(robot, reposo_pos)
    move_j(robot, punto_paso_pos)
    move_j(robot, prepick_der_pos)
    herramienta_pos.MoveJ(herramienta_pos_abierta)  # Abrir pinza
    move_l(robot, pick_der_pos)
    time.sleep(0.5)
    herramienta_pos.MoveJ(herramienta_pos_cerrada)  # Cerrar pinza
    bote_con_tapa.rdk_item.setParentStatic(herramienta_pos)
    time.sleep(0.5)
    move_l(robot, post_pick_der_pos)
    move_j(robot, punto_paso_pos)

def pick_agitador_izq_ext(robot, bote_con_tapa):
    RDK = robolink.Robolink()
    reposo_pos = RDK.Item("[EXTERIOR]Reposo", robolink.ITEM_TYPE_TARGET)
    punto_paso_pos = RDK.Item("[EXTERIOR]PuntoPaso", robolink.ITEM_TYPE_TARGET)
    base_frame_pos = RDK.Item("[EXTERIOR]Pick&PlaceAgitador", robolink.ITEM_TYPE_FRAME)
    prepick_izq_pos = RDK.Item("[EXTERIOR]PrePlaceAgitadoraIzquierda", robolink.ITEM_TYPE_TARGET)
    pick_izq_pos = RDK.Item("[EXTERIOR]PlaceAgitadoraIzquierda", robolink.ITEM_TYPE_TARGET)
    post_pick_izq_pos = prepick_izq_pos
    herramienta_pos = RDK.Item("[EXTERIOR]PinzaCobot", robolink.ITEM_TYPE_ROBOT)

    if not (reposo_pos.Valid() and punto_paso_pos.Valid() and prepick_izq_pos.Valid() and pick_izq_pos.Valid() and post_pick_izq_pos.Valid() and herramienta_pos.Valid() and base_frame_pos.Valid()):
        RDK.ShowMessage("Alguno de los targets no es válido en pick_agitador_izq_ext")
        return
    robot.setPoseFrame(base_frame_pos)

    move_j(robot, reposo_pos)
    move_j(robot, punto_paso_pos)
    move_j(robot, prepick_izq_pos)
    herramienta_pos.MoveJ(herramienta_pos_abierta)  # Abrir pinza
    move_l(robot, pick_izq_pos)
    time.sleep(0.5)
    herramienta_pos.MoveJ(herramienta_pos_cerrada)  # Cerrar pinza
    bote_con_tapa.rdk_item.setParentStatic(herramienta_pos)
    time.sleep(0.5)
    move_l(robot, post_pick_izq_pos)
    move_j(robot, punto_paso_pos)

def place_pedestal_int(robot, bote_con_tapa):
    RDK = robolink.Robolink()
    reposo_pos = RDK.Item("[INTERIOR]Reposo", robolink.ITEM_TYPE_TARGET)
    punto_paso_pos = RDK.Item("[INTERIOR]PuntoPaso", robolink.ITEM_TYPE_TARGET)
    base_frame_pos = RDK.Item("[INTERIOR]Pick&PlaceAgitador", robolink.ITEM_TYPE_FRAME)
    preplace_pos = RDK.Item("[INTERIOR]PrePlacePaletizador", robolink.ITEM_TYPE_TARGET)
    place_pos = RDK.Item("[INTERIOR]PlacePaletizador", robolink.ITEM_TYPE_TARGET)
    post_place_pos = preplace_pos
    pedestal_frame = RDK.Item("[PALETIZAR]PedestalInterior", robolink.ITEM_TYPE_FRAME)
    herramienta_pos = RDK.Item("[INTERIOR]PinzaCobot", robolink.ITEM_TYPE_ROBOT)

    if not (reposo_pos.Valid() and punto_paso_pos.Valid() and preplace_pos.Valid() and place_pos.Valid() and post_place_pos.Valid() and pedestal_frame.Valid() and herramienta_pos.Valid()):
        RDK.ShowMessage("Alguno de los targets no es válido en place_pedestal_int")
        return

    robot.setPoseFrame(base_frame_pos)
    move_j(robot, punto_paso_pos)

    robot.setPoseFrame(pedestal_frame)

    move_j(robot, preplace_pos)
    move_l(robot, place_pos)
    time.sleep(0.5)
    bote_con_tapa.rdk_item.setParentStatic(pedestal_frame)
    herramienta_pos.MoveJ(herramienta_pos_abierta)  # Abrir pinza
    time.sleep(0.5)
    move_l(robot, post_place_pos)
    herramienta_pos.MoveJ(herramienta_pos_cerrada)  # Cerrar pinza
    robot.setPoseFrame(base_frame_pos)
    move_j(robot, punto_paso_pos)
    move_j(robot, reposo_pos)

def place_pedestal_ext(robot, bote_con_tapa):
    RDK = robolink.Robolink()
    reposo_pos = RDK.Item("[EXTERIOR]Reposo", robolink.ITEM_TYPE_TARGET)
    punto_paso_pos = RDK.Item("[EXTERIOR]PuntoPaso", robolink.ITEM_TYPE_TARGET)
    base_frame_pos = RDK.Item("[EXTERIOR]Pick&PlaceAgitador", robolink.ITEM_TYPE_FRAME)
    preplace_pos = RDK.Item("[EXTERIOR]PrePlacePaletizador", robolink.ITEM_TYPE_TARGET)
    place_pos = RDK.Item("[EXTERIOR]PlacePaletizador", robolink.ITEM_TYPE_TARGET)
    post_place_pos = preplace_pos
    pedestal_frame = RDK.Item("[PALETIZAR]PedestalExterior", robolink.ITEM_TYPE_FRAME)
    herramienta_pos = RDK.Item("[EXTERIOR]PinzaCobot", robolink.ITEM_TYPE_ROBOT)

    if not (reposo_pos.Valid() and punto_paso_pos.Valid() and preplace_pos.Valid() and place_pos.Valid() and post_place_pos.Valid() and pedestal_frame.Valid() and herramienta_pos.Valid()):
        RDK.ShowMessage("Alguno de los targets no es válido en place_pedestal_ext")
        return

    robot.setPoseFrame(base_frame_pos)
    move_j(robot, punto_paso_pos)

    robot.setPoseFrame(pedestal_frame)

    move_j(robot, preplace_pos)
    move_l(robot, place_pos)
    time.sleep(0.5)
    bote_con_tapa.rdk_item.setParentStatic(pedestal_frame)
    herramienta_pos.MoveJ(herramienta_pos_abierta)  # Abrir pinza
    time.sleep(0.5)
    move_l(robot, post_place_pos)
    herramienta_pos.MoveJ(herramienta_pos_cerrada)  # Cerrar pinza
    robot.setPoseFrame(base_frame_pos)
    move_j(robot, punto_paso_pos)
    move_j(robot, reposo_pos)