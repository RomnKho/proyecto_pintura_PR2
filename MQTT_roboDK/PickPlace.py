import time
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()

# FUNCIONES DE PICK & PLACE DE SCARA

def scara_pick(tapa):

    scara = RDK.Item("Scara", ITEM_TYPE_ROBOT)
    ventosa = RDK.Item("[SCARA] Ventosa", ITEM_TYPE_TOOL)
    frame_pick = RDK.Item("[TAPAS] FramePick", ITEM_TYPE_FRAME)
    prePick = RDK.Item("[TAPAS] PrePick", ITEM_TYPE_TARGET)
    pick = RDK.Item("[TAPAS] Pick", ITEM_TYPE_TARGET)
    postPick = RDK.Item("[TAPAS] PostPick", ITEM_TYPE_TARGET)

    if not (scara.Valid() and frame_pick.Valid() and prePick.Valid() and pick.Valid() and postPick.Valid()):
        RDK.ShowMessage("Algo no es valido en scara_pick")
        return

    scara.setPoseFrame(frame_pick) # Cambio el sistema de referencia

    scara.MoveJ(prePick)           # Pick entero
    time.sleep(0.2)
    scara.MoveJ(pick)
    tapa.setParentStatic(ventosa)
    time.sleep(0.2)
    scara.MoveJ(postPick)

def scara_place_interior(tapa, tam):

    scara = RDK.Item("Scara", ITEM_TYPE_ROBOT)
    frame_place = RDK.Item(f"[INTERIOR] FramePlace{tam}", ITEM_TYPE_FRAME)
    prePlace = RDK.Item(f"[INTERIOR] PrePlace{tam}", ITEM_TYPE_TARGET)
    place = RDK.Item(f"[INTERIOR] Place{tam}", ITEM_TYPE_TARGET)
    postPlace = RDK.Item(f"[INTERIOR] PostPlace{tam}", ITEM_TYPE_TARGET)
    frame_pick = RDK.Item("[TAPAS] FramePick", ITEM_TYPE_FRAME)
    prePick = RDK.Item("[TAPAS] PrePick", ITEM_TYPE_TARGET)

    if not (scara.Valid() and frame_place.Valid() and prePlace.Valid() and place.Valid() and postPlace.Valid() and frame_pick.Valid() and prePick.Valid()):
        RDK.ShowMessage("Algo no es valido en scara_place_interior")
        return

    scara.setPoseFrame(frame_place) # Cambio el sistema de referencia
    scara.MoveJ(prePlace)
    time.sleep(0.2)
    scara.MoveJ(place)
    tapa.setParentStatic(frame_place)
    time.sleep(0.2)
    scara.MoveJ(postPlace)
    time.sleep(0.2)
    scara.setPoseFrame(frame_pick)
    scara.MoveJ(prePick)

def scara_place_exterior(tapa, tam):

    scara = RDK.Item("Scara", ITEM_TYPE_ROBOT)
    frame_place = RDK.Item(f"[EXTERIOR] FramePlace{tam}", ITEM_TYPE_FRAME)
    prePlace = RDK.Item(f"[EXTERIOR] PrePlace{tam}", ITEM_TYPE_TARGET)
    place = RDK.Item(f"[EXTERIOR] Place{tam}", ITEM_TYPE_TARGET)
    postPlace = RDK.Item(f"[EXTERIOR] PostPlace{tam}", ITEM_TYPE_TARGET)
    frame_pick = RDK.Item("[TAPAS] FramePick", ITEM_TYPE_FRAME)
    prePick = RDK.Item("[TAPAS] PrePick", ITEM_TYPE_TARGET)

    if not (scara.Valid() and frame_place.Valid() and prePlace.Valid() and place.Valid() and postPlace.Valid() and frame_pick.Valid() and prePick.Valid()):
        RDK.ShowMessage("Algo no es valido en scara_place_exterior")
        return

    scara.setPoseFrame(frame_place) # Cambio el sistema de referencia

    scara.MoveJ(prePlace)
    time.sleep(0.2)
    scara.MoveJ(place)
    tapa.setParentStatic(frame_place)
    time.sleep(0.2)
    scara.MoveJ(postPlace)
    time.sleep(0.2)
    scara.setPoseFrame(frame_pick)
    scara.MoveJ(prePick)
