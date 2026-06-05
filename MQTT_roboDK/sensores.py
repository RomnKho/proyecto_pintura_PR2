# sensores.py

from robodk import robolink
import pintproyecto.init as init
import time
from queue import Empty

RDK = robolink.Robolink()


# ------------------------------------------------------------
# Nombres reales de sensores RoboDK
# ------------------------------------------------------------

SENSOR_COLOR_INT = "[INTERIOR]SensorColor"
SENSOR_FINAL_INT = "[INTERIOR]SensorFinalCarrera" # Este es el sensor de final de carrera que hay en ambas líneas, se usa para los agitadores
SENSOR_PONER_TAPA_INT = "[INTERIOR]SensorPonerTapas"
SENSOR_ETIQUETADORA_INT = "[INTERIOR]SensorEtiquetadora"
SENSOR_PALETIZADO_INT = "[INTERIOR]SensorPaletizado"

SENSOR_COLOR_EXT = "[EXTERIOR]SensorColor"
SENSOR_FINAL_EXT = "[EXTERIOR]SensorFinalCarrera" # Este es el sensor de final de carrera que hay en ambas líneas, se usa para los agitadores
SENSOR_ETIQUETADORA_EXT = "[EXTERIOR]SensorEtiquetadora"
SENSOR_PONER_TAPA_EXT = "[EXTERIOR]SensorPonerTapa"
SENSOR_PALETIZADO_EXT = "[EXTERIOR]SensorPaletizado"

SENSOR_FINAL_TAPAS = "[TAPAS]SensorFinalCarreraEstetico"


# ------------------------------------------------------------
# Helpers de sensores
# ------------------------------------------------------------

def _item_valido(item):
    try:
        return item is not None and item.Valid()
    except Exception:
        return False


def _rdk_item_de_objeto(obj):
    """
    Las colas de sensores pueden contener Bote, Tapa, BoteConTapa
    o directamente un RDK.Item. Esta función obtiene el RDK.Item real.
    """
    if obj is None:
        return None

    if hasattr(obj, "rdk_item"):
        return obj.rdk_item

    return obj


def _hay_colision(sensor_item, objeto_item):
    if not _item_valido(sensor_item) or not _item_valido(objeto_item):
        return False

    # Probamos las dos formas porque según versión de RoboDK puede variar.
    try:
        return RDK.Collision(sensor_item, objeto_item) > 0
    except Exception:
        pass

    try:
        return sensor_item.Collision(objeto_item) > 0
    except Exception:
        return False
    
def _get_child_bote(bote, child_name="_bote"):
    if bote is None or not _item_valido(bote.rdk_item):
        return None
    bote_obj = bote.rdk_item
    try:
        for child in bote_obj.Childs():
            if child_name in child.Name():
                return child
    except Exception:
        pass
    return None

# ------------------------------------------------------------
# Sensores línea interior
# ------------------------------------------------------------

def sensor_dispensador_int_collision():
    RDK_local = robolink.Robolink()
    objeto_actual = None
    colision_prev = False

    while init.running:
        if objeto_actual is None:
            try:
                objeto_actual = init.cola_sensor_dispensador_int.get(timeout=0.2)
                colision_prev = False
            except Empty:
                continue
                
        sensor_item = RDK_local.Item(SENSOR_COLOR_INT) if _item_valido(RDK_local.Item(SENSOR_COLOR_INT)) else None
        objeto_item = _rdk_item_de_objeto(objeto_actual)
        
        objeto_detectar = _get_child_bote(objeto_actual)

        if objeto_detectar is not None:
            objeto_item = objeto_detectar

        while not _hay_colision(sensor_item, objeto_item):
            if not init.running:
                return
            time.sleep(0.1)

        colision = True
        if colision and not colision_prev:
            init.sensor_dispensador_int.set()
            init.detener_cinta_int("DISP_INT", "int")
            print(f"[SENSOR] dispensador_int detectado -> {objeto_actual.id_bote}")
            objeto_actual = None
            colision_prev = False
            time.sleep(0.4)


def sensor_poner_tapa_int_collision():
    RDK_local = robolink.Robolink()
    objeto_actual = None
    colision_prev = False

    while init.running:
        if objeto_actual is None:
            try:
                objeto_actual = init.cola_sensor_poner_tapa_int.get(timeout=0.2)
                colision_prev = False
            except Empty:
                continue

        sensor_item = RDK_local.Item(SENSOR_PONER_TAPA_INT) if _item_valido(RDK_local.Item(SENSOR_PONER_TAPA_INT)) else None
        objeto_item = _rdk_item_de_objeto(objeto_actual)

        objeto_detectar = _get_child_bote(objeto_actual)

        if objeto_detectar is not None:
            objeto_item = objeto_detectar

        while not _hay_colision(sensor_item, objeto_item):
            if not init.running:
                return
            time.sleep(0.1)

        colision = True
        if colision and not colision_prev:
            init.cola_auxiliar_sensor_tapas.put(objeto_actual.tipo)
            init.sensor_poner_tapa.set()
            init.detener_cinta_int("TAPAS_INT", "int")
            print(f"[SENSOR] poner_tapa_int detectado -> {objeto_actual.id_bote}")
            objeto_actual = None
            colision_prev = False
            time.sleep(0.4)


def sensor_etiquetadora_int_collision():
    RDK_local = robolink.Robolink()
    objeto_actual = None
    colision_prev = False
    while init.running:
        if objeto_actual is None:
            try:
                objeto_actual = init.cola_sensor_etiquetadora_int.get(timeout=0.2)
                colision_prev = False
            except Empty:
                continue

        sensor_item = RDK_local.Item(SENSOR_ETIQUETADORA_INT) if _item_valido(RDK_local.Item(SENSOR_ETIQUETADORA_INT)) else None
        objeto_item = _rdk_item_de_objeto(objeto_actual)

        while not _hay_colision(sensor_item, objeto_item):
            if not init.running:
                return
            time.sleep(0.1)

        colision = True
        if colision and not colision_prev:
            init.sensor_etiquetadora_int.set()
            init.detener_cinta_int("ETIQ_INT", "int")
            print(f"[SENSOR] etiquetadora_int detectado -> {objeto_actual.id_bote}")
            objeto_actual = None
            colision_prev = False
            time.sleep(0.4)


def sensor_agitador_int_collision():
    RDK_local = robolink.Robolink()
    objeto_actual = None
    colision_prev = False
    while init.running:
        if objeto_actual is None:
            try:
                objeto_actual = init.cola_sensor_agitadores_int.get(timeout=0.2)
                colision_prev = False
            except Empty:
                continue

        sensor_item = RDK_local.Item(SENSOR_FINAL_INT) if _item_valido(RDK_local.Item(SENSOR_FINAL_INT)) else None
        objeto_item = _rdk_item_de_objeto(objeto_actual)

        while not _hay_colision(sensor_item, objeto_item):
            if not init.running:
                return
            time.sleep(0.1)

        colision = True
        if colision and not colision_prev:
            init.sensor_agitadores_int.set()
            init.detener_cinta_int("AGI_INT", "int")
            print(f"[SENSOR] agitador_int detectado -> {objeto_actual.id_bote}")
            objeto_actual = None
            colision_prev = False
            time.sleep(0.4)


def sensor_paletizador_int_collision():
    RDK_local = robolink.Robolink()
    objeto_actual = None
    colision_prev = False
    while init.running:
        if objeto_actual is None:
            try:
                objeto_actual = init.cola_sensor_paletizado_int.get(timeout=0.2)
                colision_prev = False
            except Empty:
                continue

        sensor_item = RDK_local.Item(SENSOR_PALETIZADO_INT) if _item_valido(RDK_local.Item(SENSOR_PALETIZADO_INT)) else None
        objeto_item = _rdk_item_de_objeto(objeto_actual)

        while not _hay_colision(sensor_item, objeto_item):
            if not init.running:
                return
            time.sleep(0.1)

        colision = True
        if colision and not colision_prev:
            init.sensor_paletizado_int.set()
            print(f"[SENSOR] paletizador_int detectado -> {objeto_actual.id_bote}")
            objeto_actual = None
            colision_prev = False
            time.sleep(0.4)


# ------------------------------------------------------------
# Sensores línea exterior
# ------------------------------------------------------------

def sensor_dispensador_ext_collision():
    RDK_local = robolink.Robolink()
    objeto_actual = None
    colision_prev = False
    while init.running:
        if objeto_actual is None:
            try:
                objeto_actual = init.cola_sensor_dispensador_ext.get(timeout=0.2)
                colision_prev = False
            except Empty:
                continue

        sensor_item = RDK_local.Item(SENSOR_COLOR_EXT) if _item_valido(RDK_local.Item(SENSOR_COLOR_EXT)) else None
        objeto_item = _rdk_item_de_objeto(objeto_actual)

        objeto_detectar = _get_child_bote(objeto_actual)

        if objeto_detectar is not None:
            objeto_item = objeto_detectar

        while not _hay_colision(sensor_item, objeto_item):
            if not init.running:
                return
            time.sleep(0.1)

        colision = True
        if colision and not colision_prev:
            init.sensor_dispensador_ext.set()
            init.detener_cinta_ext("DISP_EXT", "ext")
            print(f"[SENSOR] dispensador_ext detectado -> {objeto_actual.id_bote}")
            objeto_actual = None
            colision_prev = False
            time.sleep(0.4)


def sensor_poner_tapa_ext_collision():
    RDK_local = robolink.Robolink()
    objeto_actual = None
    colision_prev = False

    while init.running:
        if objeto_actual is None:
            try:
                objeto_actual = init.cola_sensor_poner_tapa_ext.get(timeout=0.2)
                colision_prev = False
            except Empty:
                continue

        sensor_item = RDK_local.Item(SENSOR_PONER_TAPA_EXT) if _item_valido(RDK_local.Item(SENSOR_PONER_TAPA_EXT)) else None
        objeto_item = _rdk_item_de_objeto(objeto_actual)

        objeto_detectar = _get_child_bote(objeto_actual)

        if objeto_detectar is not None:
            objeto_item = objeto_detectar

        while not _hay_colision(sensor_item, objeto_item):
            if not init.running:
                return
            time.sleep(0.1)

        colision = True
        if colision and not colision_prev:
            init.cola_auxiliar_sensor_tapas.put(objeto_actual.tipo)
            init.sensor_poner_tapa.set()
            init.detener_cinta_ext("TAPAS_EXT", "ext")
            print(f"[SENSOR] poner_tapa_ext detectado -> {objeto_actual.id_bote}")
            objeto_actual = None
            colision_prev = False
            time.sleep(0.4)


def sensor_etiquetadora_ext_collision():
    RDK_local = robolink.Robolink()
    objeto_actual = None
    colision_prev = False
    while init.running:
        if objeto_actual is None:
            try:
                objeto_actual = init.cola_sensor_etiquetadora_ext.get(timeout=0.2)
                colision_prev = False
            except Empty:
                continue
        sensor_item = RDK_local.Item(SENSOR_ETIQUETADORA_EXT) if _item_valido(RDK_local.Item(SENSOR_ETIQUETADORA_EXT)) else None
        objeto_item = _rdk_item_de_objeto(objeto_actual)

        while not _hay_colision(sensor_item, objeto_item):
            if not init.running:
                return
            time.sleep(0.1)

        colision = True
        if colision and not colision_prev:
            init.sensor_etiquetadora_ext.set()
            init.detener_cinta_ext("ETIQ_EXT", "ext")
            print(f"[SENSOR] etiquetadora_ext detectado -> {objeto_actual.id_bote}")
            objeto_actual = None
            colision_prev = False
            time.sleep(0.4)


def sensor_agitador_ext_collision():
    RDK_local = robolink.Robolink()
    objeto_actual = None
    colision_prev = False
    while init.running:
        if objeto_actual is None:
            try:
                objeto_actual = init.cola_sensor_agitadores_ext.get(timeout=0.2)
                colision_prev = False
            except Empty:
                continue

        sensor_item = RDK_local.Item(SENSOR_FINAL_EXT) if _item_valido(RDK_local.Item(SENSOR_FINAL_EXT)) else None
        objeto_item = _rdk_item_de_objeto(objeto_actual)

        while not _hay_colision(sensor_item, objeto_item):
            if not init.running:
                return
            time.sleep(0.1)

        colision = True
        if colision and not colision_prev:
            init.sensor_agitadores_ext.set()
            init.detener_cinta_ext("AGI_EXT", "ext")
            print(f"[SENSOR] agitador_ext detectado -> {objeto_actual.id_bote}")
            objeto_actual = None
            colision_prev = False
            time.sleep(0.4)


def sensor_paletizador_ext_collision():
    RDK_local = robolink.Robolink()
    objeto_actual = None
    colision_prev = False
    while init.running:
        if objeto_actual is None:
            try:
                objeto_actual = init.cola_sensor_paletizado_ext.get(timeout=0.2)
                colision_prev = False
            except Empty:
                continue

        sensor_item = RDK_local.Item(SENSOR_PALETIZADO_EXT) if _item_valido(RDK_local.Item(SENSOR_PALETIZADO_EXT)) else None
        objeto_item = _rdk_item_de_objeto(objeto_actual)

        while not _hay_colision(sensor_item, objeto_item):
            if not init.running:
                return
            time.sleep(0.1)

        colision = True
        if colision and not colision_prev:
            init.sensor_paletizado_ext.set()
            print(f"[SENSOR] paletizador_ext detectado -> {objeto_actual.id_bote}")
            objeto_actual = None
            colision_prev = False
            time.sleep(0.4)

# ------------------------------------------------------------
# Sensor global de tapas
# ------------------------------------------------------------

def sensor_tapas_collision():
    RDK_local = robolink.Robolink()
    objeto_actual = None
    colision_prev = False
    while init.running:
        if objeto_actual is None:
            try:
                objeto_actual = init.cola_sensor_tapas.get(timeout=0.2)
                colision_prev = False
            except Empty:
                continue

        sensor_item = RDK_local.Item(SENSOR_FINAL_TAPAS) if _item_valido(RDK_local.Item(SENSOR_FINAL_TAPAS)) else None
        objeto_item = _rdk_item_de_objeto(objeto_actual)

        while not _hay_colision(sensor_item, objeto_item):
            if not init.running:
                return
            time.sleep(0.1)

        colision = True
        if colision and not colision_prev:
            init.sensor_tapas_final.set()
            init.detener_cinta_tap("TAPAS")
            print(f"[SENSOR] tapas_final detectado -> {objeto_actual.id_tapa}")
            objeto_actual = None
            colision_prev = False
            time.sleep(0.4)