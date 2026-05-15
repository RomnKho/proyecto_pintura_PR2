import time
from robodk.robolink import *
from robodk.robomath import *
import Init

RDK = Robolink()

# FUNCIONES DE REEMPLAZO DE BOTES

def reemplazo(linea, tam, numBote, numTapa):

    if linea == "Int":
        prefijo = "[INTERIOR]"
    else:
        prefijo = "[EXTERIOR]"

    frame_spawn = RDK.Item(f"{prefijo} FrameSensorBotes", ITEM_TYPE_FRAME)
    frame_cinta = RDK.Item(f"{prefijo} FrameCinta", ITEM_TYPE_FRAME)
    bote_tapado = RDK.Item(f"BoteTapado{tam}", ITEM_TYPE_OBJECT)
    bote_sin_tapa = RDK.Item(f"Bote{tam}_{numBote}", ITEM_TYPE_OBJECT)
    tapa = RDK.Item(f"Tapa{tam}_{numTapa}", ITEM_TYPE_OBJECT)

    if not(frame_spawn.Valid() and frame_cinta.Valid() and bote_tapado.Valid() and bote_sin_tapa.Valid() and tapa.Valid()):
        RDK.ShowMessage("Algo no es valido en reemplazo")
        return

    # SPAWN
    with Init.mutex_portapapeles:
        bote_tapado.Copy()
        bote_tapado_copy = RDK.Paste(frame_spawn)
    
    bote_tapado_copy.setName(f"Tapado{tam}_{numBote}")
    bote_tapado_copy.setParentStatic(frame_cinta)

    # DESPAWN
    partes_bote = bote_sin_tapa.Childs()

    for i in range(3):
        partes_bote[i].Delete()
    
    tapa.Delete()