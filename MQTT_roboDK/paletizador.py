# You can also use the new version of the API:
from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox
RDK = robolink.Robolink()

import Init  # Importa el módulo Init para acceder a las colas, locks y eventos compartidos
import mqtt_client as mqtt
import time

TOPIC_PUB = "emqx/ESP32_R/pub/palet"  # Define el topic de publicación (puedes moverlo a Init si lo usas en varios lugares)

robot = RDK.Item('Yaskawa_Pale')  # Oculta el paletizador en la simulación

def paletizador_int():
    while Init.running:  # Asegura que el hilo se ejecute mientras la aplicación esté activa
        Init.bote_listo_robot_int.wait() # Espera la señal del sensor[cite: 17]
        Init.bote_listo_robot_int.clear()
        
        with Init.paletizador:
            with Init.actual_int_lock:
                bote = Init.actual_int # Ya tenemos los datos correctos aquí
            
            # ... Lógica de movimiento del robot y MQTT ...[cite: 17]
            Init.contador_int += 1

def paletizador_ext():
    while Init.running:  # Asegura que el hilo se ejecute mientras la aplicación esté activa
        Init.bote_listo_robot_ext.wait()    # Espera a que el bote esté listo para el robot
        Init.bote_listo_robot_ext.clear()   # Limpia el evento para la próxima

        with Init.paletizador:  # Asegura que solo un paletizador opere a la vez
            with Init.actual_ext_lock:
                bote = Init.actual_ext  # Accede a los datos del bote externo de forma segura
            
            # ... Lógica de movimiento del robot y MQTT ...
            Init.contador_ext += 1

def contadores():
    while Init.running:  # Asegura que el hilo se ejecute mientras la aplicación esté activa
        with Init.paletizador:  # Asegura que solo un paletizador opere a la vez
            if ((Init.contador_per % 27) - 2) == 0:
                mqtt.manager.publish(f"{TOPIC_PUB}_per", f"{{ \"Cantidad\" : {Init.contador_per}, \"Tipo\" : \"Personalizados\" }}")
            if ((Init.contador_ext % 27) - 2) == 0:
                mqtt.manager.publish(f"{TOPIC_PUB}_ext", f"{{ \"Cantidad\" : {Init.contador_ext}, \"Tipo\" : \"Externos\" }}")
            if ((Init.contador_int % 27) - 2) == 0:
                mqtt.manager.publish(f"{TOPIC_PUB}_int", f"{{ \"Cantidad\" : {Init.contador_int}, \"Tipo\" : \"Internos\" }}")
        time.sleep(0.5)  # Ajusta el tiempo de espera según la frecuencia de actualización deseada