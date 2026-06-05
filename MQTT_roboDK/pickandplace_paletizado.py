Type help("robodk.robolink") or help("robodk.robomath") for more information
# Press F5 to run the script
# Documentation: https://robodk.com/doc/en/RoboDK-API.html
# Reference:     https://robodk.com/doc/en/PythonAPI/robodk.html
# Note: It is not required to keep a copy of this file, your Python script is saved with your RDK project

# You can also use the new version of the API:
import json

from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox

import time
from math import pi

import pintproyecto.init as init
from pintproyecto.init import TipoBote
import pintproyecto.mqtt_client as mqtt
import pintproyecto.procesos as procesos

TOPIC_PALET_PER = "emqx/ESP32_R/pub/avisos/palet_per"

RDK = robolink.Robolink()

 # El nombre de estas dos variables deberia ir en mayuscula al ser "constantes", no lo pongo unicamente por estetica y coherencia con el resto de modulos
robot_pal = RDK.Item("[PALETIZAR]Yaskawa_Motoman_G10", robolink.ITEM_TYPE_ROBOT)
herramienta_pal = RDK.Item("[PALETIZAR]Ventosas_Paletizador", robolink.ITEM_TYPE_TOOL)

TAM_BOTES = {
    "0.5L": (95 + 15, 100 + 15), # Tamaño mas un pequeño margen
    "2L": (135 + 15, 135 + 15),
    "5L": (195 + 15, 195 + 15),
}


def validar_item(nombre, item, tipo_esperado):
    if item.Valid() and item.Type() == tipo_esperado:
        return True

    tipo_real = item.Type() if item.Valid() else "INVALIDO"
    print(f"[ERROR] Item RoboDK no válido: {nombre} | tipo esperado={tipo_esperado} | tipo real={tipo_real}")
    return False


validar_item("[PALETIZAR]Yaskawa_Motoman_G10", robot_pal, robolink.ITEM_TYPE_ROBOT)
validar_item("[PALETIZAR]Ventosas_Paletizador", herramienta_pal, robolink.ITEM_TYPE_TOOL)


class Espacio:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h


class PaletInteligente:
    def __init__(self, ancho, largo, linea):
        self.ancho = ancho
        self.largo = largo
        self.linea = linea
        self.espacios_libres = [Espacio(0, 0, self.ancho, self.largo)]
        self.botes = []

    def resetear(self):
        print(f"[INFO] Reiniciando palet inteligente de la línea {self.linea}...")
        init.numero_avisos_palet += 1
        mqtt.manager.publish(TOPIC_PALET_PER, json.dumps({"linea": self.linea, "estado": 1 ,"num_avisos": init.numero_avisos_palet}))
        print(f"AVISO: Palet lleno en línea {self.linea}. Total avisos de palet lleno: {init.numero_avisos_palet}")
        time.sleep(3)  # Simular tiempo de retirada del palet
        self.espacios_libres = [Espacio(0, 0, self.ancho, self.largo)]
        while self.botes:
            bote, _, _ = self.botes.pop()
            try:
                if bote.rdk_item is not None:
                    bote.rdk_item.Delete()
            except:
                pass
        self.botes = []
        mqtt.manager.publish(TOPIC_PALET_PER, json.dumps({"linea": self.linea, "estado": 0}))

    def encontrar_mejor_espacio(self, w_bote, h_bote):

        mejor = None
        mejor_score = float("inf")

        for espacio in self.espacios_libres:
            if espacio.w >= w_bote and espacio.h >= h_bote:
                desperdicio = (espacio.w * espacio.h) - (w_bote * h_bote)

                if desperdicio < mejor_score:
                    mejor_score = desperdicio
                    mejor = espacio

        return mejor

    def dividir_espacio(self, espacio, w_bote, h_bote):

        self.espacios_libres.remove(espacio)

        # espacio derecha
        if espacio.w > w_bote:
            self.espacios_libres.append(
                Espacio(
                    espacio.x + w_bote,
                    espacio.y,
                    espacio.w - w_bote,
                    h_bote
                )
            )

        # espacio abajo
        if espacio.h > h_bote:
            self.espacios_libres.append(
                Espacio(
                    espacio.x,
                    espacio.y + h_bote,
                    espacio.w,
                    espacio.h - h_bote
                )
            )

    def colocar_bote(self, bote):

        tam = bote.dict_bote.get("tamano")
        if tam not in TAM_BOTES:
            print(f"[ERROR] Tamaño de bote desconocido: {tam}")
            return None
        
        w_bote, h_bote = TAM_BOTES[tam]

        espacio = self.encontrar_mejor_espacio(w_bote, h_bote)

        if espacio is None: # No hay espacio suficiente para colocar el bote, se asume que el palet está lleno y se simula la retirada del palet (reset completo)
            self.resetear()
            return None

        x, y = espacio.x, espacio.y

        self.dividir_espacio(espacio, w_bote, h_bote)

        self.botes.append((bote, x, y))

        return (x, y)

 # En principio por ahora solo tendra una altura, porque al ser diferentes alturas (tamaños de botes) se complica bastante
PALET_INT = PaletInteligente(900, 600, "int")
PALET_EXT = PaletInteligente(900, 600, "ext")

# Dict para saber el nombre del item en RDK a partir del palet | dict_palet.get(palet) -> str
dict_palet = {
    PALET_EXT: "[PALETIZAR]Pale_Exterior",
    PALET_INT: "[PALETIZAR]Pale_Interior",
}

def obtener_palet_destino(bote):
    tipo = bote.tipo

    if tipo == TipoBote.EXTERIOR:
        return PALET_EXT
    elif tipo == TipoBote.INTERIOR:
        return PALET_INT
    else:
        raise ValueError(f"Tipo de bote desconocido: {tipo}")

def calcular_pose_palet(palet_item, x, y):
    """
    Calcula la pose de colocación respecto al frame [PALETIZAR]Paletizador.

    IMPORTANTE:
    - Los palets están definidos respecto a [PALETIZAR]Paletizador.
    - Por eso usamos palet_item.Pose(), NO PoseAbs().
    - Luego el robot debe tener como frame activo [PALETIZAR]Paletizador.
    """

    pose_palet_relativa = palet_item.Pose()

    # Altura de colocación respecto al origen del palet.
    desplazamiento = robomath.transl(x, y, 0)
    orientacion_ventosa = robomath.rotx(pi)  # Giro de 180 grados para que las ventosas miren hacia abajo

    pose = pose_palet_relativa * desplazamiento * orientacion_ventosa

    return pose

def move_j(robot, target):
    robot.MoveJ(target, blocking=False)
    time.sleep(0.2)

def move_l(robot, target):
    robot.MoveL(target, blocking=False)
    time.sleep(0.2)

def pick_pedestal_int(bote_con_tapa):
    if bote_con_tapa.rdk_item is None:
        print(f"[ERROR] Bote {bote_con_tapa.id_bote} no tiene rdk_item válido")
        return
    
    frame_pos = RDK.Item("[PALETIZAR]Targets", robolink.ITEM_TYPE_FRAME)
    reposo_pos = RDK.Item("[PALETIZAR]Reposo", robolink.ITEM_TYPE_TARGET)
    prepick_pos = RDK.Item("[PALETIZAR]PrePickInterior", robolink.ITEM_TYPE_TARGET)
    pick_pos = RDK.Item("[PALETIZAR]PickInterior", robolink.ITEM_TYPE_TARGET)

    if not validar_item("[PALETIZAR]Reposo", reposo_pos, robolink.ITEM_TYPE_TARGET):
        return
    if not validar_item("[PALETIZAR]PrePickInterior", prepick_pos, robolink.ITEM_TYPE_TARGET):
        return
    if not validar_item("[PALETIZAR]PickInterior", pick_pos, robolink.ITEM_TYPE_TARGET):
        return
    if not validar_item("[PALETIZAR]Ventosas_Paletizador", herramienta_pal, robolink.ITEM_TYPE_TOOL):
        return
    print(f"[DEBUG] Anterior prepick_pos: {prepick_pos.Pose()}")

    tam = procesos.normalizar_tamano(bote_con_tapa.dict_bote.get("tam", bote_con_tapa.dict_bote.get("tamano", "2L")))
    if tam == "5L":
        offset = 0
    elif tam == "2L":
        offset = 50
    else:
        offset = 100

    local_prepick = prepick_pos.Pose() * robomath.transl(0, 0, offset)
    local_pick = pick_pos.Pose() * robomath.transl(0, 0, offset)
    print(f"[DEBUG] Nuevo prepick_pos con offset {offset}: {local_prepick}")

    robot_pal.setPoseFrame(frame_pos)
    move_j(robot_pal, reposo_pos)
    move_j(robot_pal, local_prepick)
    move_j(robot_pal, local_pick) # No se puede usar movimientos lineales
    time.sleep(0.2)
    bote_con_tapa.rdk_item.setParentStatic(herramienta_pal)
    time.sleep(0.5)
    move_j(robot_pal, local_prepick)
    move_j(robot_pal, reposo_pos)

def pick_pedestal_ext(bote_con_tapa):
    if bote_con_tapa.rdk_item is None:
        print(f"[ERROR] Bote {bote_con_tapa.id_bote} no tiene rdk_item válido")
        return
    
    frame_pos = RDK.Item("[PALETIZAR]Targets", robolink.ITEM_TYPE_FRAME)
    reposo_pos = RDK.Item("[PALETIZAR]Reposo", robolink.ITEM_TYPE_TARGET)
    prepick_pos = RDK.Item("[PALETIZAR]PrePickExterior", robolink.ITEM_TYPE_TARGET)
    pick_pos = RDK.Item("[PALETIZAR]PickExterior", robolink.ITEM_TYPE_TARGET)

    if not validar_item("[PALETIZAR]Reposo", reposo_pos, robolink.ITEM_TYPE_TARGET):
        return
    if not validar_item("[PALETIZAR]PrePickExterior", prepick_pos, robolink.ITEM_TYPE_TARGET):
        return
    if not validar_item("[PALETIZAR]PickExterior", pick_pos, robolink.ITEM_TYPE_TARGET):
        return
    if not validar_item("[PALETIZAR]Ventosas_Paletizador", herramienta_pal, robolink.ITEM_TYPE_TOOL):
        return
    
    tam = procesos.normalizar_tamano(bote_con_tapa.dict_bote.get("tam", bote_con_tapa.dict_bote.get("tamano", "2L")))
    if tam == "5L":
        offset = 0
    elif tam == "2L":
        offset = 50
    else:
        offset = 100
    
    local_prepick = prepick_pos.Pose() * robomath.transl(0, 0, offset)
    local_pick = pick_pos.Pose() * robomath.transl(0, 0, offset)

    robot_pal.setPoseFrame(frame_pos)
    move_j(robot_pal, reposo_pos)
    move_j(robot_pal, local_prepick)
    move_j(robot_pal, local_pick)
    time.sleep(0.2)
    bote_con_tapa.rdk_item.setParentStatic(herramienta_pal)
    time.sleep(0.5)
    move_j(robot_pal, local_prepick)
    move_j(robot_pal, reposo_pos)

def obtener_posicion_paletizado(bote):
    palet = obtener_palet_destino(bote)
    pos = palet.colocar_bote(bote)

    if pos is None:
        print("[INFO] Palet lleno. Simulando retirada del palet...")
        time.sleep(2)

        for b, _, _ in palet.botes:
            try:
                if b.rdk_item is not None:
                    b.rdk_item.Delete()
            except:
                pass

        palet.resetear()
        pos = palet.colocar_bote(bote)

    if pos is not None:
        palet_name = dict_palet.get(palet)
        palet_item = RDK.Item(palet_name, robolink.ITEM_TYPE_FRAME)

        if not validar_item(palet_name, palet_item, robolink.ITEM_TYPE_FRAME):
            return (None, None, None)

        x, y = pos
        pose = calcular_pose_palet(palet_item, x, y)

        return (pose, palet_item, palet)

    print(f"[ERROR] No se pudo obtener posición válida para el bote {bote.id_bote}")
    return (None, None, None)

def paletizar_bote(bote):
    if bote.rdk_item is None or not bote.rdk_item.Valid():
        print(f"[ERROR] Bote {bote.id_bote} no tiene rdk_item válido")
        return
    raw_tam = bote.dict_bote.get("tam", bote.dict_bote.get("tamano", "2L"))
    print(f"[DEBUG] Bote {bote.id_bote} dict_bote: {bote.dict_bote}")
    print(f"[DEBUG] raw_tam antes normalizar: {raw_tam!r}")
    tam = procesos.normalizar_tamano(raw_tam)
    print(f"[DEBUG] tam normalizado: {tam}")
    tipo = bote.tipo
    if tipo == TipoBote.INTERIOR:
        with init.cintas_lock:
            init.cinta_interior_running = False
    elif tipo == TipoBote.EXTERIOR:
        with init.cintas_lock:
            init.cinta_exterior_running = False
    if tam not in TAM_BOTES:
        print(f"[ERROR] Tamaño de bote desconocido: {tam}")
        return
    _, h = TAM_BOTES[tam]
    print(f"Altura del bote para paletizado: {h}")
    
    pose, palet_item, _ = obtener_posicion_paletizado(bote)

    if pose is None:
        print(f"[ERROR] No se pudo obtener posición de paletizado para el bote {bote.id_bote}")
        return
    
    frame_paletizador = RDK.Item("[PALETIZAR]Paletizador", robolink.ITEM_TYPE_FRAME)
    reposo_pos = RDK.Item("[PALETIZAR]Reposo", robolink.ITEM_TYPE_TARGET)

    if not validar_item("[PALETIZAR]Paletizador", frame_paletizador, robolink.ITEM_TYPE_FRAME):
        return
    if not validar_item("[PALETIZAR]Reposo", reposo_pos, robolink.ITEM_TYPE_TARGET):
        return
    
    if palet_item is None or not palet_item.Valid():
        print(f"[ERROR] palet_item es None o inválido para el bote {bote.id_bote}")
        return
    
    robot_pal.setPoseFrame(frame_paletizador)
    robot_pal.setPoseTool(herramienta_pal)

    print("Frame activo del robot: [PALETIZAR]Paletizador")
    print(f"Palet destino: {palet_item.Name()}")
    print(f"Pose de place relativa al paletizador:\n{pose}")
    # Elevar la pose, ya que el punto de referencia del place del bote es a nivel del suelo y queremos colocar el bote sobre el palet, no hundirlo en el palet. El valor de h depende del tamaño del bote.
    pose = pose * robomath.transl(0, 0, -h)
    print(f"Pose de place elevada:\n{pose}")
    pre_place = pose * robomath.transl(0, 0, -250)
    post_place = pre_place

    print(f"Pre-place:\n{pre_place}")

    move_j(robot_pal, reposo_pos)
    move_j(robot_pal, pre_place)
    move_j(robot_pal, pose)
    time.sleep(1)
    bote.rdk_item.setParentStatic(palet_item)
    time.sleep(0.5)
    move_j(robot_pal, post_place)
    move_j(robot_pal, reposo_pos)
