# Type help("robodk.robolink") or help("robodk.robomath") for more information
# Press F5 to run the script
# Documentation: https://robodk.com/doc/en/RoboDK-API.html
# Reference:     https://robodk.com/doc/en/PythonAPI/robodk.html
# Note: It is not required to keep a copy of this file, your Python script is saved with your RDK project

# You can also use the new version of the API:
from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox
RDK = robolink.Robolink()

import threading
import time

cinta_int = RDK.Item("[INTERIOR]CintaMovil")
cinta_ext = RDK.Item("[EXTERIOR]CintaMovil")
cinta_tap = RDK.Item("[TAPAS]CintaTapa")

if not cinta_int.Valid():
    raise Exception("No se encontró la cinta interior")
if not cinta_ext.Valid():
    raise Exception("No se encontró la cinta exterior")
if not cinta_tap.Valid():
    raise Exception("No se encontró la cinta de tapas")

def cinta_exterior():
    while True:
        pos_actual = cinta_ext.Joints().list()  # Obtiene la posición actual de las articulaciones
        pos_actual[0] += 1  # Incrementa solo la primera articulación
        cinta_ext.MoveJ(pos_actual, blocking=False)  # Mueve la cinta exterior sin bloquear el hilo
        time.sleep(0.001) # Simula el tiempo que tarda la cinta exterior en procesar un producto

def cinta_interior():
    while True:
        pos_actual = cinta_int.Joints().list()  # Obtiene la posición actual de las articulaciones
        pos_actual[0] += 1  # Incrementa solo la primera articulación
        cinta_int.MoveJ(pos_actual, blocking=False)  # Mueve la cinta interior sin bloquear el hilo
        time.sleep(0.001) # Simula el tiempo que tarda la cinta interior en procesar un producto

def cinta_tapas():
    while True:
        pos_actual = cinta_tap.Joints().list()  # Obtiene la posición actual de las articulaciones
        pos_actual[0] += 1  # Incrementa solo la primera articulación
        cinta_tap.MoveJ(pos_actual, blocking=False)  # Mueve la cinta de tapas sin bloquear el hilo
        time.sleep(0.001) # Simula el tiempo que tarda la cinta de tapas en procesar un producto

# Crear hilos para cada cinta
hilo_cinta_ext = threading.Thread(target=cinta_exterior)
hilo_cinta_int = threading.Thread(target=cinta_interior)
hilo_cinta_tap = threading.Thread(target=cinta_tapas)

# Iniciar los hilos
hilo_cinta_ext.start()
hilo_cinta_int.start()
hilo_cinta_tap.start()

# Esperar a que los hilos terminen (en este caso, nunca terminarán), simualremos la detención al pulsar una tecla
try:
    while True:
        time.sleep(1)  # Mantiene el programa principal activo
except KeyboardInterrupt:
    print("Deteniendo las cintas...")