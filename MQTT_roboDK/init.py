import json
import threading
from queue import Queue
import enum
import time

import pintproyecto.mqtt_client as mqtt

TOPIC_RGB_PUB = "emqx/ESP32_R/pub/avisos/rgb_per"

class TipoBote(enum.Enum):
    INTERIOR = 0
    EXTERIOR = 1

class estadoAgitador(enum.Enum):
    LIBRE = 0
    OCUPADO = 1

class Agitador(enum.Enum):
    DER_INT = 0
    IZQ_INT = 1
    DER_EXT = 2
    IZQ_EXT = 3

def _normalizar_tipo(valor):
    if isinstance(valor, TipoBote):
        return valor

    texto = str(valor).strip().lower()
    if texto in ["interior", "int"]:
        return TipoBote.INTERIOR
    return TipoBote.EXTERIOR


class Bote:
    def __init__(self, id_bote, dict_bote, rdk_item):
        self.id_bote = id_bote
        self.dict_bote = dict_bote
        self.rdk_item = rdk_item

        self.tipo = _normalizar_tipo(dict_bote.get('tipo', 'interior'))


class Tapa:
    def __init__(self, id_tapa, tipo, rdk_item):
        self.id_tapa = id_tapa
        self.tipo = _normalizar_tipo(tipo)
        self.rdk_item = rdk_item


class BoteConTapa:
    def __init__(self, id_bote, id_tapa, dict_bote, rdk_item):
        self.id_bote = id_bote
        self.id_tapa = id_tapa
        self.dict_bote = dict_bote
        self.rdk_item = rdk_item

        self.tipo = _normalizar_tipo(dict_bote.get('tipo', 'interior'))

class BoteConEtiqueta:
    def __init__(self, id_bote, dict_bote, rdk_item):
        self.id_bote = id_bote
        self.dict_bote = dict_bote
        self.rdk_item = rdk_item

        self.tipo = _normalizar_tipo(dict_bote.get('tipo', 'interior'))

class RGBColor:
    def __init__(self, r=2000, g=2000, b=2000):
        self.r = r
        self.g = g
        self.b = b

    def avisar_color_agotado(self, tipo):
        global numero_avisos_rgb

        if self.r <= 0:
            numero_avisos_rgb += 1
            mqtt.manager.publish(TOPIC_RGB_PUB, json.dumps({"color_agotado": "rojo", "linea": tipo.name.lower(), "num_avisos": numero_avisos_rgb}))
            print(f"AVISO: Color rojo agotado en línea {tipo.name.lower()}. Total avisos RGB: {numero_avisos_rgb}")
            self.r = 2000
        if self.g <= 0:
            numero_avisos_rgb += 1
            mqtt.manager.publish(TOPIC_RGB_PUB, json.dumps({"color_agotado": "verde", "linea": tipo.name.lower(), "num_avisos": numero_avisos_rgb}))
            print(f"AVISO: Color verde agotado en línea {tipo.name.lower()}. Total avisos RGB: {numero_avisos_rgb}")
            self.g = 2000
        if self.b <= 0:
            numero_avisos_rgb += 1
            mqtt.manager.publish(TOPIC_RGB_PUB, json.dumps({"color_agotado": "azul", "linea": tipo.name.lower(), "num_avisos": numero_avisos_rgb}))
            print(f"AVISO: Color azul agotado en línea {tipo.name.lower()}. Total avisos RGB: {numero_avisos_rgb}")
            self.b = 2000

    # En este método se descuentan las cantidades de color usadas en cada bote, PROBARLO
    def descontar(self, tipo=None, r=0, g=0, b=0): 
        self.r = self.r - r
        self.g = self.g - g
        self.b = self.b - b
        print(f"Descontando color para línea {tipo.name.lower() if tipo else 'desconocida'}: R-{r}, G-{g}, B-{b}. Colores restantes: R={self.r}, G={self.g}, B={self.b}")

        if self.r < 0 or self.g < 0 or self.b < 0:
            self.avisar_color_agotado(tipo)




# ------------------------------------------------------------
# Control general
# ------------------------------------------------------------

running = True

cinta_exterior_running = False
cinta_interior_running = False
cinta_tapas_running = False

cinta_int_lock = threading.Lock() 
cinta_ext_lock = threading.Lock() 
cinta_tapas_lock = threading.Lock() 

cintas_lock = threading.Lock()

global_tapas_generadas = 0
numero_avisos_tapas = 0
numero_avisos_rgb = 0
numero_avisos_palet = 0

id_bote_actual = 0
id_tapa_actual = 0

id_lock = threading.Lock()
encolar_lock = threading.Lock()
copy_paste_lock = threading.Lock()
contador_lock = threading.Lock()
agitadores_lock = threading.Lock()
gen_tapas_lock = threading.Lock()
deteccion_lock = threading.Lock()

# ------------------------------------------------------------
# MQTT -> 2 colas de pedidos
# ------------------------------------------------------------

cola_general_int = Queue()
cola_general_ext = Queue()

# ------------------------------------------------------------
# Colas del proceso productivo
# ------------------------------------------------------------

cola_dispensador_int = Queue()
cola_dispensador_ext = Queue()

# Cola de tapas única/global
cola_tapas = Queue()

# Botes pintados esperando a que se coloque su tapa
cola_esperar_tapa_int = Queue()
cola_esperar_tapa_ext = Queue()

# Pares (bote, tapa) esperando etiquetadora
cola_etiquetadora_int = Queue()
cola_etiquetadora_ext = Queue()

# BotesConTapa esperando agitadores
cola_agitadores_int = Queue()
cola_agitadores_ext = Queue()

# Tuplas (bote_con_tapa, agitador, segundos)
cola_proceso_agitador_int = Queue()
cola_proceso_agitador_ext = Queue()

# Tuplas (bote_con_tapa, agitador) para sacar de agitador
cola_salida_agitador_int = Queue()
cola_salida_agitador_ext = Queue()

# Paletizado
cola_paletizado_int = Queue()
cola_paletizado_ext = Queue()


# ------------------------------------------------------------
# Colas de objetos a detectar por cada sensor
# IMPORTANTE:
# Cada sensor mira su cola en orden FIFO.
# Esto evita que 4 botes seguidos sobrescriban una única variable detectar_*.
# ------------------------------------------------------------

cola_sensor_dispensador_int = Queue()
cola_sensor_dispensador_ext = Queue()

cola_sensor_poner_tapa_int = Queue()
cola_sensor_poner_tapa_ext = Queue()

cola_sensor_tapas = Queue()

cola_auxiliar_sensor_tapas = Queue()

cola_sensor_etiquetadora_int = Queue()
cola_sensor_etiquetadora_ext = Queue()

cola_sensor_agitadores_int = Queue()
cola_sensor_agitadores_ext = Queue()

cola_sensor_paletizado_int = Queue()
cola_sensor_paletizado_ext = Queue()


# ------------------------------------------------------------
# Estado de agitadores: False = ocupado, True = libre
# ------------------------------------------------------------

estado_agitador_der_int = estadoAgitador.LIBRE
estado_agitador_izq_int = estadoAgitador.LIBRE
estado_agitador_der_ext = estadoAgitador.LIBRE
estado_agitador_izq_ext = estadoAgitador.LIBRE
agitadores_lock = threading.Lock()

estado_pedestal_paletizado_int = True # True = pedestal libre, False = pedestal ocupado (esperando a que se paletice el bote para liberar)
estado_pedestal_paletizado_ext = True


estado_pedestal_int_lock = threading.Lock()
estado_pedestal_ext_lock = threading.Lock()

# ------------------------------------------------------------
# Sincronización generación-cintas
# ------------------------------------------------------------
# ------------------------------------------------------------
# Sincronización generación-cintas
# ------------------------------------------------------------

# Línea exterior
cinta_ext_lista_para_generar = threading.Event()
bote_ext_generado_event = threading.Event()
pedido_ext_pendiente_generacion = threading.Event()

# Línea interior
cinta_int_lista_para_generar = threading.Event()
bote_int_generado_event = threading.Event()
pedido_int_pendiente_generacion = threading.Event()

# Cinta global de tapas
pedido_tapa_pendiente_generacion = threading.Event()
cinta_tap_lista_para_generar = threading.Event()
tapa_generada_event = threading.Event()

tapas_first = True

# ------------------------------------------------------------
# Eventos de paletizado (Borrado/Vaciado)
# ------------------------------------------------------------

aviso_vaciar_palet_int = threading.Event()
aviso_vaciar_palet_ext = threading.Event()
aviso_vaciar_palet_per = threading.Event()

# ------------------------------------------------------------
# Eventos de sensores
# ------------------------------------------------------------

sensor_dispensador_int = threading.Event()
sensor_dispensador_ext = threading.Event()

sensor_tapas_final = threading.Event()

sensor_poner_tapa = threading.Event()

sensor_etiquetadora_int = threading.Event()
sensor_etiquetadora_ext = threading.Event()

sensor_agitadores_int = threading.Event()
sensor_agitadores_ext = threading.Event()

sensor_paletizado_int = threading.Event()
sensor_paletizado_ext = threading.Event()

solicitante_actual_int = None
solicitante_actual_ext = None
solicitante_actual_tap = None

bloqueadores_cinta_int = set()
bloqueadores_cinta_ext = set()
bloqueadores_cinta_tap = set()

def detener_cinta_int(solicitante: str, cinta: str):
    global cinta_interior_running, solicitante_actual_int

    with cintas_lock:
        bloqueadores_cinta_int.add(solicitante)
        cinta_interior_running = False
        solicitante_actual_int = ",".join(bloqueadores_cinta_int)

        print(f"{solicitante} ha detenido la cinta {cinta}.")
        print(f"[INT] Bloqueadores activos: {bloqueadores_cinta_int}")


def reanudar_cinta_int(solicitante: str, cinta: str):
    global cinta_interior_running, solicitante_actual_int

    with cintas_lock:
        if solicitante not in bloqueadores_cinta_int:
            print(f"[INT] {solicitante} quiso reanudar, pero no estaba bloqueando la cinta.")
            print(f"[INT] Bloqueadores activos: {bloqueadores_cinta_int}")
            return

        bloqueadores_cinta_int.remove(solicitante)

        if len(bloqueadores_cinta_int) == 0:
            cinta_interior_running = True
            solicitante_actual_int = None
            print(f"{solicitante} ha reanudado la cinta {cinta}.")
        else:
            cinta_interior_running = False
            solicitante_actual_int = ",".join(bloqueadores_cinta_int)
            print(f"{solicitante} ha terminado, pero la cinta {cinta} sigue parada.")
            print(f"[INT] Siguen bloqueando: {bloqueadores_cinta_int}")

def detener_cinta_ext(solicitante: str, cinta: str):
    global cinta_exterior_running, solicitante_actual_ext

    with cintas_lock:
        bloqueadores_cinta_ext.add(solicitante)
        cinta_exterior_running = False
        solicitante_actual_ext = ",".join(bloqueadores_cinta_ext)

        print(f"{solicitante} ha detenido la cinta {cinta}.")
        print(f"[EXT] Bloqueadores activos: {bloqueadores_cinta_ext}")


def reanudar_cinta_ext(solicitante: str, cinta: str):
    global cinta_exterior_running, solicitante_actual_ext

    with cintas_lock:
        if solicitante not in bloqueadores_cinta_ext:
            print(f"[EXT] {solicitante} quiso reanudar, pero no estaba bloqueando la cinta.")
            print(f"[EXT] Bloqueadores activos: {bloqueadores_cinta_ext}")
            return

        bloqueadores_cinta_ext.remove(solicitante)

        if len(bloqueadores_cinta_ext) == 0:
            cinta_exterior_running = True
            solicitante_actual_ext = None
            print(f"{solicitante} ha reanudado la cinta {cinta}.")
        else:
            cinta_exterior_running = False
            solicitante_actual_ext = ",".join(bloqueadores_cinta_ext)
            print(f"{solicitante} ha terminado, pero la cinta {cinta} sigue parada.")
            print(f"[EXT] Siguen bloqueando: {bloqueadores_cinta_ext}")

def detener_cinta_tap(solicitante: str):
    global cinta_tapas_running, solicitante_actual_tap

    with cintas_lock:
        bloqueadores_cinta_tap.add(solicitante)
        cinta_tapas_running = False
        solicitante_actual_tap = ",".join(bloqueadores_cinta_tap)

        print(f"{solicitante} ha detenido la cinta de tapas.")
        print(f"[TAPAS] Bloqueadores activos: {bloqueadores_cinta_tap}")


def reanudar_cinta_tap(solicitante: str):
    global cinta_tapas_running, solicitante_actual_tap

    with cintas_lock:
        if solicitante not in bloqueadores_cinta_tap:
            print(f"[TAPAS] {solicitante} quiso reanudar, pero no estaba bloqueando la cinta.")
            print(f"[TAPAS] Bloqueadores activos: {bloqueadores_cinta_tap}")
            return

        bloqueadores_cinta_tap.remove(solicitante)

        if len(bloqueadores_cinta_tap) == 0:
            cinta_tapas_running = True
            solicitante_actual_tap = None
            print(f"{solicitante} ha reanudado la cinta de tapas.")
        else:
            cinta_tapas_running = False
            solicitante_actual_tap = ",".join(bloqueadores_cinta_tap)
            print(f"{solicitante} ha terminado, pero la cinta de tapas sigue parada.")
            print(f"[TAPAS] Siguen bloqueando: {bloqueadores_cinta_tap}")

def vaciar_cola(q):
    while not q.empty():
        try:
            q.get_nowait()
        except Exception:
            break

def reset_init():
    global running
    global cinta_exterior_running, cinta_interior_running, cinta_tapas_running
    global id_bote_actual, id_tapa_actual
    global estado_agitador_der_int, estado_agitador_izq_int
    global estado_agitador_der_ext, estado_agitador_izq_ext
    global estado_pedestal_paletizado_int, estado_pedestal_paletizado_ext
    global solicitante_actual_int, solicitante_actual_ext, solicitante_actual_tap

    running = False
    cinta_exterior_running = False
    cinta_interior_running = False
    cinta_tapas_running = False
    time.sleep(1)  # Pequeña espera para que los hilos lean el cambio en 'running' y terminen

    id_bote_actual = 0
    id_tapa_actual = 0

    estado_agitador_der_int = estadoAgitador.LIBRE
    estado_agitador_izq_int = estadoAgitador.LIBRE
    estado_agitador_der_ext = estadoAgitador.LIBRE
    estado_agitador_izq_ext = estadoAgitador.LIBRE

    estado_pedestal_paletizado_int = True
    estado_pedestal_paletizado_ext = True

    for evento in [
    sensor_dispensador_int,
    sensor_dispensador_ext,
    sensor_tapas_final,
    sensor_poner_tapa,
    sensor_etiquetadora_int,
    sensor_etiquetadora_ext,
    sensor_agitadores_int,
    sensor_agitadores_ext,
    sensor_paletizado_int,
    sensor_paletizado_ext,

    # Eventos generación botes
    cinta_ext_lista_para_generar,
    bote_ext_generado_event,
    pedido_ext_pendiente_generacion,

    cinta_int_lista_para_generar,
    bote_int_generado_event,
    pedido_int_pendiente_generacion,

    # Eventos generación tapas
    pedido_tapa_pendiente_generacion,
    cinta_tap_lista_para_generar,
    tapa_generada_event,
]:
        evento.clear()
    bloqueadores_cinta_int.clear()
    bloqueadores_cinta_ext.clear()
    bloqueadores_cinta_tap.clear()

    solicitante_actual_int = None
    solicitante_actual_ext = None
    solicitante_actual_tap = None

    for q in [
         cola_general_int, cola_general_ext,
        cola_dispensador_int, cola_dispensador_ext,
        cola_tapas,
        cola_esperar_tapa_int, cola_esperar_tapa_ext,
        cola_etiquetadora_int, cola_etiquetadora_ext,
        cola_agitadores_int, cola_agitadores_ext,
        cola_proceso_agitador_int, cola_proceso_agitador_ext,
        cola_salida_agitador_int, cola_salida_agitador_ext,
        cola_paletizado_int, cola_paletizado_ext,
        cola_sensor_dispensador_int, cola_sensor_dispensador_ext,
        cola_sensor_poner_tapa_int, cola_sensor_poner_tapa_ext,
        cola_sensor_tapas,
        cola_sensor_etiquetadora_int, cola_sensor_etiquetadora_ext,
        cola_sensor_agitadores_int, cola_sensor_agitadores_ext,
        cola_sensor_paletizado_int, cola_sensor_paletizado_ext,
    ]:
        vaciar_cola(q)
