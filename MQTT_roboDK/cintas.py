from robodk import robolink
from robodk import robomath
import pintproyecto.init as init
import time

INCREMENTO = 300

def mover_cinta_ext():
    RDK = robolink.Robolink()
    cinta_ext = RDK.Item("[EXTERIOR]CintaMovil")

    if not cinta_ext.Valid():
        raise Exception("No se encontró la cinta exterior")

    while init.running:
        with init.cintas_lock:
            puede_mover = (
                init.cinta_exterior_running
                and len(init.bloqueadores_cinta_ext) == 0
            )

        if puede_mover:
            pos_actual = cinta_ext.Joints()
            cinta_ext.MoveJ(pos_actual + INCREMENTO)

            # Si hay un pedido ya cogido por el generador esperando a ser generado
            if init.pedido_ext_pendiente_generacion.is_set():
                with init.cintas_lock:
                    init.cinta_exterior_running = False

                print("[SYNC EXT] Cinta exterior parada para generar.")

                # MUY IMPORTANTE:
                # Limpio antes de esperar para no consumir un evento viejo
                init.bote_ext_generado_event.clear()

                # Aviso al generador
                init.cinta_ext_lista_para_generar.set()

                # Espero a que genere
                init.bote_ext_generado_event.wait()
                init.bote_ext_generado_event.clear()

                with init.cintas_lock:
                    if len(init.bloqueadores_cinta_ext) == 0:
                        init.cinta_exterior_running = True
                        print("[SYNC EXT] Bote generado. Cinta exterior reanudada.")
                    else:
                        init.cinta_exterior_running = False
                        print(f"[SYNC EXT] Cinta exterior sigue bloqueada por {init.bloqueadores_cinta_ext}")

            time.sleep(0.001)

        else:
            time.sleep(0.05)



def mover_cinta_int():
    RDK = robolink.Robolink()
    cinta_int = RDK.Item("[INTERIOR]CintaMovil")

    if not cinta_int.Valid():
        raise Exception("No se encontró la cinta interior")

    while init.running:
        with init.cintas_lock:
            puede_mover = (
                init.cinta_interior_running
                and len(init.bloqueadores_cinta_int) == 0
            )

        if puede_mover:
            pos_actual = cinta_int.Joints()
            cinta_int.MoveJ(pos_actual + INCREMENTO)

            # Si hay un pedido ya cogido por el generador esperando a ser generado
            if init.pedido_int_pendiente_generacion.is_set():
                with init.cintas_lock:
                    init.cinta_interior_running = False

                print("[SYNC INT] Cinta interior parada para generar.")

                # MUY IMPORTANTE:
                # Limpio antes de esperar para no consumir un evento viejo
                init.bote_int_generado_event.clear()

                # Aviso al generador
                init.cinta_int_lista_para_generar.set()

                # Espero a que genere
                init.bote_int_generado_event.wait()
                init.bote_int_generado_event.clear()

                with init.cintas_lock:
                    if len(init.bloqueadores_cinta_int) == 0:
                        init.cinta_interior_running = True
                        print("[SYNC INT] Bote generado. Cinta interior reanudada.")
                    else:
                        init.cinta_interior_running = False
                        print(f"[SYNC INT] Cinta interior sigue bloqueada por {init.bloqueadores_cinta_int}")

            time.sleep(0.001)

        else:
            time.sleep(0.05)


def mover_cinta_tapas():
    RDK = robolink.Robolink()
    cinta_tap = RDK.Item("[TAPAS]CintaMovil")

    if not cinta_tap.Valid():
        raise Exception("No se encontró la cinta de tapas")

    while init.running:
        with init.cintas_lock:
            puede_mover = (
                init.cinta_tapas_running
                and len(init.bloqueadores_cinta_tap) == 0
            )

        if puede_mover:
            pos_actual = cinta_tap.Joints()
            cinta_tap.MoveJ(pos_actual + INCREMENTO)

            # Si hay una tapa esperando a generarse,
            # paro en múltiplo de 300 para generar.
            if init.pedido_tapa_pendiente_generacion.is_set():
                with init.cintas_lock:
                    init.cinta_tapas_running = False

                print("[SYNC TAPAS] Cinta de tapas parada para generar.")

                # Limpio evento viejo
                init.tapa_generada_event.clear()

                # Aviso al generador de tapas
                init.cinta_tap_lista_para_generar.set()

                # Espero a que la tapa se genere
                init.tapa_generada_event.wait()
                init.tapa_generada_event.clear()

                with init.cintas_lock:
                    if len(init.bloqueadores_cinta_tap) == 0:
                        init.cinta_tapas_running = True
                        print("[SYNC TAPAS] Tapa generada. Cinta de tapas reanudada.")
                    else:
                        init.cinta_tapas_running = False
                        print(f"[SYNC TAPAS] Tapa generada, pero cinta de tapas sigue bloqueada por {init.bloqueadores_cinta_tap}")

            time.sleep(0.001)

        else:
            time.sleep(0.05)