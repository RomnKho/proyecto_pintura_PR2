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

import json
# import mqtt_client as mqtt # Por ahora es opcional
import threading

from queue import Empty

import time
import random

INTERIOR = 1
EXTERIOR = 2

"""Funciones para la generación de botes y tapas, así como para el manejo de las colas de productos a fabricar y en proceso de fabricación. 
Estas funciones se ejecutan en hilos separados para permitir la concurrencia en la generación y manejo de productos en ambas líneas de producción (interna y externa)."""

def encolar_linea(data, tipo, linea) -> int:
    try:
        if linea == "int":
            if tipo == "per": 
                init.cola_per_int.put(data)
            else: 
                init.cola_gen_int.put(data)
        elif linea == "ext":
                if tipo == "per": 
                    init.cola_per_ext.put(data)
                else: 
                    init.cola_gen_ext.put(data)
        return 0
    except: return 1


def handle_message(mqttc, topic, payload):
    data = json.loads(payload)
    tipo = data.get("tipo")
    linea = data.get("linea")
    err = encolar_linea(data, tipo, linea)
    if err != 0:
        print("Error: No se pudo encolar el producto")

 # ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ #
def generar_b_int():
    while init.running:
        bote = init.cola_productos_int.get() # Espera a que desencolar_int le mande trabajo

        tamano = bote.get("tamano")
        bote_obj = RDK.Item(f"Bote_{tamano}L")
        tapa_obj = RDK.Item(f"Tapa_{tamano}L")

        # --TODO: Terminar el proceso de generacion de botes de la linea interior -----------------------------------------------------

        bote_obj.Copy()
        bote_copy = RDK.Paste()

        bote_copy.setName(f"CBote_Int")
        bote_copy.setParent(RDK.Item("[INTERIOR]FrameCinta_Static"))

        bote_copy.setPose(pose=robomath.eye()) # Ajusta la posición del bote copiado para que no se superponga con el original

        bote_copy.setParentStatic(RDK.Item("[INTERIOR]FrameCinta"))
        ... # Aqui iria el proceso de colocacion del bote en la cinta transportadora, pero por ahora solo se genera el bote y se le asigna un nombre unico para luego poder manipularlo con el robot.

        init.cola_actual_int.put(bote)
            
    # WARNING: Problema de superposicion de tapas, ya que puede ser que las tapas de la linea interior y exterior se creen a la vez o intercaladamente, haciendo que se superpongan y que luego el robot no sepa cual es cual.
        with init.cola_tapas_lock:
            tapa_obj.Copy()
            tapa_copy = RDK.Paste()

            tapa_copy.setName(f"CTapa_Int")
            tapa_copy.setParent(RDK.Item("[TAPAS]FrameCinta_Static"))

            tapa_copy.setPose(pose=robomath.eye()) # Ajusta la posición de la tapa copiada para que no se superponga con el original

            tapa_copy.setParentStatic(RDK.Item("[TAPAS]FrameCinta"))
            init.cola_tapas.put(INTERIOR) # Se agraga la linea de la cola para que luego el scara sepa a que linea pertenece la tapa que va a manipular
                
        time.sleep(30) # Espera un tiempo antes de generar el siguiente producto para evitar un uso excesivo de CPU y para simular un proceso de generación más realista
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ #

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ #

def generar_b_ext():
    while init.running:
        bote = init.cola_productos_ext.get() # Espera a que desencolar_ext le mande trabajo
        tamano = bote.get("tamano")
        bote_obj = RDK.Item(f"Bote_{tamano}L")
        tapa_obj = RDK.Item(f"Tapa_{tamano}L")

        # --TODO: Terminar el proceso de generacion de botes de la linea exterior -----------------------------------------------------
        bote_obj.Copy()
        bote_copy = RDK.Paste()

        bote_copy.setName(f"CBote_Ext")
        bote_copy.setParent(RDK.Item("[EXTERIOR]FrameCinta_Static"))

        bote_copy.setPose(pose=robomath.eye()) # Ajusta la posición del bote copiado para que no se superponga con el original

        bote_copy.setParentStatic(RDK.Item("[EXTERIOR]FrameCinta"))
        ... # Aqui iria el proceso de colocacion del bote en la cinta transportadora, pero por ahora solo se genera el bote y se le asigna un nombre unico para luego poder manipularlo con el robot.
        init.cola_actual_ext.put(bote)

        with init.cola_tapas_lock:
            tapa_obj.Copy()
            tapa_copy = RDK.Paste()

            tapa_copy.setName(f"CTapa_Ext")
            tapa_copy.setParent(RDK.Item("[TAPAS]FrameCinta_Static"))

            tapa_copy.setPose(pose=robomath.eye()) # Ajusta la posición de la tapa copiada para que no se superponga con el original

            tapa_copy.setParentStatic(RDK.Item("[TAPAS]FrameCinta"))
            init.cola_tapas.put(EXTERIOR) # Se agraga la linea de la cola para que luego el scara sepa a que linea pertenece la tapa que va a manipular

            time.sleep(30) # Espera un tiempo antes de generar el siguiente producto para evitar un uso excesivo de CPU y para simular un proceso de generación más realista
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ #

def encolar_procesados_int(bote: dict, cantidad: int):
        for _ in range(cantidad):
            init.cola_productos_int.put(bote.copy())

def encolar_procesados_ext(bote:dict, cantidad: int):
        for _ in range(cantidad):
            init.cola_productos_ext.put(bote.copy())

def desencolar_int():
    while init.running:
        if not init.cola_per_int.empty():
            data = init.cola_per_int.get()
        else:
            data = init.cola_gen_int.get() # Aquí el hilo se queda pausado si no hay nada
        
        cantidad = data.get("cantidad", 0)
        encolar_procesados_int(data, cantidad) # Se encolan los productos procesados para que el hilo de generación los copie y los coloque en la cinta transportadora

def desencolar_ext():
    while init.running:
        if not init.cola_per_ext.empty():
            data = init.cola_per_ext.get()
        else:
            data = init.cola_gen_ext.get() # Aquí el hilo se queda pausado si no hay nada
        
        cantidad = data.get("cantidad", 0)
        encolar_procesados_ext(data, cantidad) # Se encolan los productos procesados para que el hilo de generación los copie y los coloque en la cinta transportadora
        

def actual_cinta_int():
    while init.running:
        bote_en_camino = init.cola_actual_int.get()

        with init.actual_int_lock:
            init.actual_int = bote_en_camino

        # Esta seccion se desbloqueara luego de que el sensor final (antes del paletizado) detecte el porducto, lo que indicara que ya se ha fabricado el producto y otro mas puede encabezar su proceso de fabricacion
        init.bote_procesado_int.wait() # El hilo se bloquea aquí hasta que el evento bote_procesado_int sea seteado, lo que indicará que el producto actual ha sido procesado y otro puede encabezar su proceso de fabricación
        init.bote_procesado_int.clear() # Se limpia el evento para que el hilo pueda volver a esperar por el siguiente producto a procesar

def actual_cinta_ext():
    while init.running:
        bote_en_camino = init.cola_actual_ext.get()

        with init.actual_ext_lock:
            init.actual_ext = bote_en_camino

        # Esta seccion se desbloqueara luego de que el sensor final (antes del paletizado) detecte el porducto, lo que indicara que ya se ha fabricado el producto y otro mas puede encabezar su proceso de fabricacion
        init.bote_procesado_ext.wait() # El hilo se bloquea aquí hasta que el evento bote_procesado_ext sea seteado, lo que indicará que el producto actual ha sido procesado y otro puede encabezar su proceso de fabricación
        init.bote_procesado_ext.clear() # Se limpia el evento para que el hilo pueda volver a esperar por el siguiente producto a procesar

def generator_gen():
    while init.running:
        numero_tamaño = random.randint(0, 2)
        numero_linea = random.randint(0, 1)
        tamano = ["Pequeño", "Mediano", "Grande"][numero_tamaño]
        linea = ["int", "ext"][numero_linea]
        cantidad = random.randint(1, 5)
        data = {
            "tipo": "gen",
            "linea": linea,
            "tamano": tamano,
            "cantidad": cantidad
        }
        err = encolar_linea(data, "gen", linea)
        if err != 0:
            print("Error: No se pudo encolar el producto")
        time.sleep(10) # Espera un tiempo antes de generar el siguiente producto para evitar un uso excesivo de CPU y para simular un proceso de generación más realista

threading.Thread(target=generator_gen, daemon=True).start()
threading.Thread(target=actual_cinta_int, daemon=True).start()
threading.Thread(target=actual_cinta_ext, daemon=True).start()
threading.Thread(target=desencolar_int, daemon=True).start()
threading.Thread(target=desencolar_ext, daemon=True).start()
threading.Thread(target=generar_b_int, daemon=True).start()
threading.Thread(target=generar_b_ext, daemon=True).start()

try:
    while init.running:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("Programa terminado por el usuario")