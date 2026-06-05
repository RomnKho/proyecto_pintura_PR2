# main.py
# Arranque principal de la simulación RoboDK mediante hilos

import threading
import time
import traceback

import init
import procesos as p
import sensores as s
import cintas

import mqtt_client
import mqttListener

import pickandplace_agitadores
import pickandplace_paletizado
import pickandplace_tapas
import reset as r


# ------------------------------------------------------------
# Configuración
# ------------------------------------------------------------

HILOS_DAEMON = True

# ------------------------------------------------------------
# Utilidades para hilos
# ------------------------------------------------------------

def ejecutar_seguro(nombre, funcion):
    """
    Ejecuta una función dentro de un hilo y muestra el error
    si ese hilo falla, para saber exactamente qué proceso se ha roto.
    """
    try:
        print(f"[MAIN] Hilo iniciado: {nombre}")
        funcion()
    except Exception as e:
        print(f"[MAIN][ERROR] El hilo '{nombre}' se ha detenido: {e}")
        traceback.print_exc()


def crear_hilo(nombre, funcion):
    return threading.Thread(
        target=ejecutar_seguro,
        args=(nombre, funcion),
        name=nombre,
        daemon=HILOS_DAEMON
    )


def iniciar_hilos(hilos):
    for hilo in hilos:
        hilo.start()
        time.sleep(0.05)


def existe_funcion(modulo, nombre):
    return hasattr(modulo, nombre) and callable(getattr(modulo, nombre))


def crear_hilo_si_existe(nombre_hilo, modulo, nombre_funcion):
    """
    Crea el hilo solo si la función existe.
    Así el main.py no revienta si todavía no has implementado
    algún sensor o proceso concreto.
    """
    if existe_funcion(modulo, nombre_funcion):
        return crear_hilo(nombre_hilo, getattr(modulo, nombre_funcion))

    print(f"[MAIN][AVISO] No existe la función {nombre_funcion}(). No se crea el hilo: {nombre_hilo}")
    return None


# ------------------------------------------------------------
# Sensores
# ------------------------------------------------------------

def crear_hilos_sensores():
    hilos = []

    funciones_sensores = [
        # Línea interior
        ("Sensor dispensador/color interior", s, "sensor_dispensador_int_collision"),
        ("Sensor poner tapa interior", s, "sensor_poner_tapa_int_collision"),
        ("Sensor etiquetadora/final carrera interior", s, "sensor_etiquetadora_int_collision"),
        ("Sensor agitador interior", s, "sensor_agitador_int_collision"),
        ("Sensor paletizado interior", s, "sensor_paletizador_int_collision"),

        # Línea exterior
        ("Sensor dispensador/color exterior", s, "sensor_dispensador_ext_collision"),
        ("Sensor poner tapa exterior", s, "sensor_poner_tapa_ext_collision"),
        ("Sensor etiquetadora/final carrera exterior", s, "sensor_etiquetadora_ext_collision"),
        ("Sensor agitador exterior", s, "sensor_agitador_ext_collision"),
        ("Sensor paletizado exterior", s, "sensor_paletizador_ext_collision"),

        # Cinta global de tapas
        ("Sensor final carrera tapas", s, "sensor_tapas_collision"),
    ]

    for nombre_hilo, modulo, nombre_funcion in funciones_sensores:
        hilo = crear_hilo_si_existe(nombre_hilo, modulo, nombre_funcion)
        if hilo is not None:
            hilos.append(hilo)

    return hilos


# ------------------------------------------------------------
# Procesos de la línea
# ------------------------------------------------------------

def crear_hilos_procesos():
    hilos = []

    funciones_procesos = [
        # Generación
        ("Generación botes interior", p, "generar_botes_int"),
        ("Generación botes exterior", p, "generar_botes_ext"),

        # Dispensadores / color
        ("Dispensador interior", p, "dispensador_int"),
        ("Dispensador exterior", p, "dispensador_ext"),

        # Cinta global de tapas
        ("Colocar tapas", p, "colocar_tapas"),

        # Etiquetado
        ("Etiquetadora interior", p, "etiquetador_botes_int"),
        ("Etiquetadora exterior", p, "etiquetador_botes_ext"),

        # Agitadores fase 1: meter bote
        ("Poner agitador interior", p, "poner_agitadores_int"),
        ("Poner agitador exterior", p, "poner_agitadores_ext"),

        # Agitadores fase 2: esperar tiempo
        ("Esperar agitación interior", p, "esperar_agitacion_int"),
        ("Esperar agitación exterior", p, "esperar_agitacion_ext"),

        # Sacar botes de agitadores
        ("Sacar botes agitados interior", p, "sacar_botes_agitados_int"),
        ("Sacar botes agitados exterior", p, "sacar_botes_agitados_ext"),

        # Paletizado
        ("Paletizado interior", p, "paletizado_int"),
        ("Paletizado exterior", p, "paletizado_ext"),
    ]

    for nombre_hilo, modulo, nombre_funcion in funciones_procesos:
        hilo = crear_hilo_si_existe(nombre_hilo, modulo, nombre_funcion)
        if hilo is not None:
            hilos.append(hilo)

    return hilos

def crear_hilos_cintas():
    hilos = []

    if cintas is None:
        print("[MAIN][AVISO] Cintas no iniciado: módulo cintas no disponible")
        return hilos

    funciones_cintas = [
        ("Mover cinta interior", cintas, "mover_cinta_int"),
        ("Mover cinta exterior", cintas, "mover_cinta_ext"),
        ("Mover cinta tapas", cintas, "mover_cinta_tapas"),
    ]

    for nombre_hilo, modulo, nombre_funcion in funciones_cintas:
        hilo = crear_hilo_si_existe(nombre_hilo, modulo, nombre_funcion)
        if hilo is not None:
            hilos.append(hilo)

    return hilos


# ------------------------------------------------------------
# MQTT
# ------------------------------------------------------------

def iniciar_mqtt():
    if mqttListener is None:
        print("[MAIN][AVISO] MQTT no iniciado: mqttListener no está disponible")
        return

    if existe_funcion(mqttListener, "iniciar_mqtt"):
        try:
            mqttListener.iniciar_mqtt()
            print("[MAIN] MQTT iniciado")
        except Exception as e:
            print(f"[MAIN][ERROR] No se pudo iniciar MQTT: {e}")
            traceback.print_exc()
    else:
        print("[MAIN][AVISO] mqttListener no tiene iniciar_mqtt()")


def detener_mqtt():
    try:
        if mqtt_client is not None and hasattr(mqtt_client, "manager"):
            mqtt_client.manager.disconnect()
            print("[MAIN] MQTT desconectado")
    except Exception as e:
        print(f"[MAIN][AVISO] No se pudo desconectar MQTT: {e}")


# ------------------------------------------------------------
# Parada segura
# ------------------------------------------------------------

def desbloquear_eventos():
    """
    Desbloquea todos los .wait() de los procesos para que puedan salir
    cuando init.running pase a False.
    """
    posibles_eventos = [
        "sensor_dispensador_int",
        "sensor_dispensador_ext",
        "sensor_tapas_final",
        "sensor_poner_tapa_int",
        "sensor_poner_tapa_ext",
        "sensor_etiquetadora_int",
        "sensor_etiquetadora_ext",
        "sensor_agitadores_int",
        "sensor_agitadores_ext",
        "sensor_paletizado_int",
        "sensor_paletizado_ext",
    ]

    for nombre_evento in posibles_eventos:
        if hasattr(init, nombre_evento):
            try:
                getattr(init, nombre_evento).set()
            except Exception:
                pass


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    print("==================================================")
    print("       INICIANDO SIMULACIÓN ROBO DK")
    print("==================================================")

    init.running = True

    # OJO: si iniciar_sensores() espera a que existan objetos como
    # CBote_Int, CBote_Ext o CTapa y todavía no existen, puede bloquearse.
    if existe_funcion(s, "iniciar_sensores"):
        try:
            print("[MAIN] Inicializando sensores base...")
            s.iniciar_sensores()
            print("[MAIN] Sensores base inicializados")
        except Exception as e:
            print(f"[MAIN][AVISO] Error inicializando sensores base: {e}")
            traceback.print_exc()

    hilos = []
    hilos.extend(crear_hilos_sensores())
    hilos.extend(crear_hilos_procesos())
    hilos.extend(crear_hilos_cintas())

    print(f"[MAIN] Arrancando {len(hilos)} hilos...")
    iniciar_hilos(hilos)

    iniciar_mqtt()

    print("==================================================")
    print("       SIMULACIÓN INICIADA")
    print("==================================================")
    print("[MAIN] Pulsa CTRL+C para detener la simulación")

    try:
        while init.running:
            time.sleep(1)

    except KeyboardInterrupt:
        r.reset()

    finally:
        init.running = False
        init.cinta_exterior_running = False
        init.cinta_interior_running = False
        init.cinta_tapas_running = False
        desbloquear_eventos()
        detener_mqtt()
        print("[MAIN] Simulación detenida")


if __name__ == "__main__":
    main()