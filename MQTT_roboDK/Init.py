# Script de inicializacion

import threading
from queue import Queue

# Variable global para controlar la ejecución de los hilos
running = True

# Colas para la informacion del pedido
cola_info_pedido_interior = Queue()
cola_info_pedido_exterior = Queue()

# Colas para los botes que se generan
cola_bote_pintura_interior = Queue()
cola_bote_pintura_exterior = Queue()

# Colas con el bote a pintar
cola_bote_a_pintar_interior = Queue()
cola_bote_a_pintar_exterior = Queue()

# Cola con los colores a pintar
cola_colores_interior = Queue()
cola_colores_exterior = Queue()

# Colas de entrada (MQTT y Generador Genérico)
cola_gen_int = Queue()
cola_per_int = Queue()
cola_gen_ext = Queue()
cola_per_ext = Queue()

# Colas de fabricación técnica (Lo que RoboDK debe copiar/pegar)
cola_productos_int = Queue()
cola_productos_ext = Queue()

# Colas de seguimiento físico (Lo que YA está en la cinta)
cola_actual_int = Queue()
cola_actual_ext = Queue()

# Cola de tapas para el SCARA
cola_tapas = Queue()
cola_tapas_lock = threading.Lock()  # Lock para la cola de tapas, ya que es un recurso compartido entre ambos generadores

# Variables de estado (Seguimos necesitando Locks para diccionarios/contadores simples)
actual_int = {}
actual_ext = {}
actual_int_lock = threading.Lock()
actual_ext_lock = threading.Lock()

# Eventos de sincronización (Sensores)
bote_procesado_int = threading.Event()
bote_procesado_ext = threading.Event()
bote_listo_robot_int = threading.Event()
bote_listo_robot_ext = threading.Event()

# Contadores y Mutex del robot paletizador
contador_int = 0
contador_ext = 0
contador_per = 0
paletizador = threading.Lock()

def clean_init():
    global contador_ext, contador_int, contador_per, running
    
    # Limpiar todas las colas
    for q in [cola_gen_int, cola_per_int, cola_gen_ext, cola_per_ext, 
              cola_productos_int, cola_productos_ext, 
              cola_actual_int, cola_actual_ext, 
              cola_tapas]:
        with q.mutex:
            q.queue.clear()
            q.all_tasks_done.notify_all()
            q.unfinished_tasks = 0

    # Limpiar diccionarios de estado
    actual_int.clear()
    actual_ext.clear()

    # Limpiar eventos
    bote_listo_robot_ext.clear()
    bote_listo_robot_int.clear()
    bote_procesado_ext.clear()
    bote_procesado_int.clear()

    # Resetear contadores
    contador_ext = 0
    contador_int = 0
    contador_per = 0