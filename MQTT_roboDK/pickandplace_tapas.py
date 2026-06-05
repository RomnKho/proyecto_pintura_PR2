import time

from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox

import pintproyecto.init
from pintproyecto.init import TipoBote

RDK = robolink.Robolink()
scara = RDK.Item("Scara", robolink.ITEM_TYPE_ROBOT)

def move_j(robot, target):
    robot.MoveJ(target, blocking=False)
    time.sleep(0.2)

def move_l(robot, target):
    robot.MoveL(target, blocking=False)
    time.sleep(0.2)

def pickandplace_tapa(tapa, bote, tipo):
    scara_pick(tapa)
    tamano = bote.dict_bote.get("tamano")

    if tipo == TipoBote.INTERIOR:
        scara_place_interior(tapa, tamano)
    else:
        scara_place_exterior(tapa, tamano)

def scara_pick(tapa):
    ventosa = RDK.Item("[SCARA]Ventosa", robolink.ITEM_TYPE_TOOL)
    frame_pick = RDK.Item("[TAPAS]FramePick", robolink.ITEM_TYPE_FRAME)
    prePick = RDK.Item("[TAPAS]PrePick", robolink.ITEM_TYPE_TARGET)
    pick = RDK.Item("[TAPAS]Pick", robolink.ITEM_TYPE_TARGET)
    postPick = prePick

    if not (scara.Valid() and frame_pick.Valid() and prePick.Valid() and pick.Valid() and postPick.Valid()):
        RDK.ShowMessage("Algo no es valido en scara_pick")
        return

    scara.setPoseFrame(frame_pick)
    move_j(scara, prePick)
    move_l(scara, pick)
    time.sleep(0.5)
    tapa.rdk_item.setParentStatic(ventosa)
    time.sleep(0.5)
    move_l(scara, postPick)

def scara_place_interior(tapa, tam):
    frame_place = RDK.Item(f"[INTERIOR]FramePlace{tam}", robolink.ITEM_TYPE_FRAME)
    prePlace = RDK.Item(f"[INTERIOR]PrePlace{tam}", robolink.ITEM_TYPE_TARGET)
    place = RDK.Item(f"[INTERIOR]Place{tam}", robolink.ITEM_TYPE_TARGET)
    postPlace = prePlace
    frame_cinta = RDK.Item("[INTERIOR]FrameCinta", robolink.ITEM_TYPE_FRAME)

    frame_pick = RDK.Item("[TAPAS]FramePick", robolink.ITEM_TYPE_FRAME)
    prePick = RDK.Item("[TAPAS]PrePick", robolink.ITEM_TYPE_TARGET)

    if not (frame_place.Valid() and prePlace.Valid() and place.Valid() and postPlace.Valid()):
        RDK.ShowMessage("Algo no es valido en scara_place_interior")
        return

    scara.setPoseFrame(frame_place) # Cambio el sistema de referencia
    move_j(scara, prePlace)
    move_l(scara, place)
    time.sleep(0.5)
    tapa.rdk_item.setParentStatic(frame_cinta)
    time.sleep(0.5)
    move_l(scara, postPlace)

    scara.setPoseFrame(frame_pick)
    move_j(scara, prePick)

def scara_place_exterior(tapa, tam):
    frame_place = RDK.Item(f"[EXTERIOR]FramePlace{tam}", robolink.ITEM_TYPE_FRAME)
    prePlace = RDK.Item(f"[EXTERIOR]PrePlace{tam}", robolink.ITEM_TYPE_TARGET)
    place = RDK.Item(f"[EXTERIOR]Place{tam}", robolink.ITEM_TYPE_TARGET)
    postPlace = prePlace
    frame_cinta = RDK.Item("[EXTERIOR]FrameCinta", robolink.ITEM_TYPE_FRAME)

    frame_pick = RDK.Item("[TAPAS]FramePick", robolink.ITEM_TYPE_FRAME)
    prePick = RDK.Item("[TAPAS]PrePick", robolink.ITEM_TYPE_TARGET)

    if not (frame_place.Valid() and prePlace.Valid() and place.Valid() and postPlace.Valid()):
        RDK.ShowMessage("Algo no es valido en scara_place_exterior")
        return

    scara.setPoseFrame(frame_place) # Cambio el sistema de referencia

    move_j(scara, prePlace)
    move_l(scara, place)
    time.sleep(0.5)
    tapa.rdk_item.setParentStatic(frame_cinta)
    time.sleep(0.5)
    move_l(scara, postPlace)

    scara.setPoseFrame(frame_pick)
    move_j(scara, prePick)