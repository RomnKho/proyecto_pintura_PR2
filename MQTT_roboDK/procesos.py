# procesos.py

from robodk import robolink
from robodk import robomath

import pintproyecto.init as init
from pintproyecto.init import TipoBote, estadoAgitador, Agitador
from pintproyecto.init import Bote, Tapa, BoteConTapa, BoteConEtiqueta

import pintproyecto.mqtt_client as mqtt


import json
import time
import random
from queue import Empty


import pintproyecto.pickandplace_tapas as tap
import pintproyecto.pickandplace_agitadores as agi
import pintproyecto.pickandplace_paletizado as pal


RDK = robolink.Robolink()

TOPIC_TAPAS_PUB = "emqx/ESP32_R/pub/avisos/tapas_per"
TOPIC_PALET_PER_PUB = "emqx/ESP32_R/pub/avisos/palet_per"
TOPIC_PROD_PUB = "emqx/ESP32_R/pub/prod_per"
TOPIC_FINALIZADO_PUB = "emqx/ESP32_R/pub/finalizado_per"

# ------------------------------------------------------------
# Nombres de modelos/referencias RoboDK
# Ajusta solo estos nombres si cambian en la estación.
# ------------------------------------------------------------

REF_GEN_BOTE_INT = "[INTERIOR]FrameCinta_Static"
REF_GEN_BOTE_EXT = "[EXTERIOR]FrameCinta_Static"
REF_GEN_TAPA = "[TAPAS]FrameCinta_Static"

REF_BOTE_CON_TAPA_INT = "[INTERIOR]FramePonerTapas_Static"
REF_BOTE_CON_TAPA_EXT = "[EXTERIOR]FramePonerTapas_Static"

REF_BOTE_CON_ETIQUETA_INT = "[INTERIOR]FrameEtiquetador_Static"
REF_BOTE_CON_ETIQUETA_EXT = "[EXTERIOR]FrameEtiquetador_Static"

REF_CINTA_EXT = "[EXTERIOR]FrameCinta"
REF_CINTA_INT = "[INTERIOR]FrameCinta"
REF_CINTA_TAPAS = "[TAPAS]FrameCinta"

rbg_int = init.RGBColor()
rbg_ext = init.RGBColor()

def normalizar_tamano(tam):
    tam = str(tam).strip()
    mapa = {
        "G": "5L", "M": "2L", "P": "0.5L",
        "g": "5L", "m": "2L", "p": "0.5L",
        "grande": "5L", "mediano": "2L",
        "pequeno": "0.5L", "pequeño": "0.5L",
    }
    return mapa.get(tam, tam if tam in ["5L", "2L", "0.5L"] else "2L")


def obtener_modelo_bote(tam):
    tam = normalizar_tamano(tam)
    if tam == "5L":
        return "BotePintura5L"
    elif tam == "2L":
        return "BotePintura2L"
    elif tam == "0.5L":
        return "BotePintura0.5L"
    return "BotePintura2L"


def obtener_modelo_tapa(tam):
    tam = normalizar_tamano(tam)
    if tam == "5L":
        return "Tapa5L"
    elif tam == "2L":
        return "Tapa2L"
    elif tam == "0.5L":
        return "Tapa0.5L"
    return "Tapa2L"


def obtener_modelo_bote_tapa(tam):
    tam = normalizar_tamano(tam)
    if tam == "5L":
        return "BotePinturaTapa5L"
    elif tam == "2L":
        return "BotePinturaTapa2L"
    elif tam == "0.5L":
        return "BotePinturaTapa0.5L"
    return "BotePinturaTapa2L"

def obtener_modelo_bote_etiqueta(tam):
    tam = normalizar_tamano(tam)
    if tam == "5L":
        return "BoteTapaEtiqueta5L"
    elif tam == "2L":
        return "BoteTapaEtiqueta2L"
    elif tam == "0.5L":
        return "BoteTapaEtiqueta0.5L"
    return "BoteTapaEtiqueta2L"


# ------------------------------------------------------------
# Helpers RoboDK
# ------------------------------------------------------------

def obtener_item(nombre):
    if nombre is None:
        return None

    item = RDK.Item(nombre)
    try:
        if item.Valid():
            return item
        else:
            print(f"[DEBUG] Item '{nombre}' NO es válido (no existe)")
            return None
    except Exception as e:
        print(f"[DEBUG] Error al obtener item '{nombre}': {e}")
        return None

    print(f"[AVISO] No se encontró el item RoboDK: {nombre}")
    return None


def copiar_item(nombre_base, tamano, nuevo_nombre, ref_nombre_static=None, ref_nombre_cinta=None):
    with init.copy_paste_lock:
        base = obtener_item(nombre_base)
        if base is None:
            print(f"[ERROR] Modelo base '{nombre_base}' no encontrado")
            return None

        try:
            RDK.Copy(base)
            nuevo = RDK.Paste()
        except Exception as e:
            print(f"[ERROR] No se pudo copiar/pegar modelo '{nombre_base}': {e}")
            return None
            
        nuevo.setName(nuevo_nombre)

        ref_static = obtener_item(ref_nombre_static) if ref_nombre_static else None
        ref_cinta = obtener_item(ref_nombre_cinta) if ref_nombre_cinta else None
        
        if ref_nombre_static and ref_static is None:
            print(f"[ADVERTENCIA] Referencia estática '{ref_nombre_static}' no encontrada en copiar_item()")
        if ref_nombre_cinta and ref_cinta is None:
            print(f"[ADVERTENCIA] Referencia de cinta '{ref_nombre_cinta}' no encontrada en copiar_item()")
        
        if ref_static is not None:
            try:
                nuevo.setParent(ref_static)
                nuevo.setPose(pose=robomath.eye())
            except Exception as e:
                print(f"[ERROR] No se pudo asignar parent a {nuevo_nombre}: {e}")

        # Dependiendo del tamaño del bote se le debe poner un OFFSET para que se ajuste al centro de la cinta transportadora
        if tamano == "5L":
            offset = 0.0
        elif tamano == "2L":
            offset = 30.0
        else :
            offset = 50.0
        pose = ref_cinta.Pose() * robomath.transl(0, offset, 0)
        nuevo.setPose(pose=pose)

        if ref_cinta is not None:
            try:
                nuevo.setParentStatic(ref_cinta)
            except Exception as e:
                print(f"[ERROR] No se pudo asignar parent estático a {nuevo_nombre}: {e}")

        return nuevo


def hex_to_rgba(hex_color):
    try:
        hex_color = str(hex_color).strip().replace("#", "")
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        return [r, g, b, 1]
    except Exception:
        return [1, 1, 1, 1]


def buscar_child_item(parent, texto_nombre):
    if parent is None:
        return None

    try:
        for child in parent.Childs():
            if texto_nombre in child.Name():
                return child
    except Exception:
        pass

    return None


def set_color_bote(bote):
    if bote is None or bote.rdk_item is None:
        return
    
    color = bote.dict_bote.get("rgb_hex", bote.dict_bote.get("color", None))
    if color is None:
        print(f"[AVISO] Bote {bote.id_bote} sin color")
        return

    tam = normalizar_tamano(bote.dict_bote.get("tam", bote.dict_bote.get("tamano", "2L")))
    nombre_pintura = f"BotePintura{tam}_pintura"

    pintura = buscar_child_item(bote.rdk_item, nombre_pintura)
    if pintura is None:
        pintura = buscar_child_item(bote.rdk_item, "_pintura")

    if pintura is None:
        print(f"[ERROR] No se encontró child de pintura en bote {bote.id_bote}")
        return
    rgba_decimal = [int(color[i:i+2], 16) for i in range(0, 6, 2)] # Valores de color en decimal (0-255) para descontar del RGB general
    rgba = hex_to_rgba(color) # Para RoboDK
    tipo = bote.tipo
    if tipo == TipoBote.INTERIOR:
        rbg_int.descontar(tipo=tipo, r=int(rgba_decimal[0]), g=int(rgba_decimal[1]), b=int(rgba_decimal[2]))
    else:
        rbg_ext.descontar(tipo=tipo, r=int(rgba_decimal[0]), g=int(rgba_decimal[1]), b=int(rgba_decimal[2]))
    try:
        pintura.setColor(rgba)
        print(f"[COLOR] Bote {bote.id_bote} pintado con {color}")
    except Exception as e:
        print(f"[ERROR] No se pudo pintar bote {bote.id_bote}: {e}")


def crear_bote_con_tapa_visual(bote, tapa, tipo):
    tam = bote.dict_bote.get("tam", bote.dict_bote.get("tamano", "2L"))
    modelo_final = obtener_modelo_bote_tapa(tam)
    nombre_final = f"CBoteConTapa_{bote.id_bote}_{tapa.id_tapa}"
    print(f"Control 1 - Modelo: {modelo_final}, Nombre final: {nombre_final}")

    if tipo == TipoBote.INTERIOR:
        ref_bote = REF_BOTE_CON_TAPA_INT
        ref_cinta = REF_CINTA_INT
    else:
        ref_bote = REF_BOTE_CON_TAPA_EXT
        ref_cinta = REF_CINTA_EXT

    print(f"  ref_bote={ref_bote}, ref_cinta={ref_cinta}")
    item_final = copiar_item(modelo_final, tam,  nombre_final, ref_nombre_static=ref_bote, ref_nombre_cinta=ref_cinta)
    if item_final is None or not item_final.Valid():
        print(f"[ERROR] No se pudo crear el item final para BoteConTapa {bote.id_bote}/{tapa.id_tapa}")
        return None

    print(f"Control 2")
    try:

        # Obtener y eliminar hijos de forma iterativa por si hay anidamiento
        while True:
            hijos = bote.rdk_item.Childs()
            if not hijos:
                break
            for hijo in hijos:
                hijo.Delete()
        bote.rdk_item.Delete()
    except Exception as e:
        print(f"[ERROR] No se pudo eliminar bote: {e}")

    print(f"Control 3")
    try:
        tapa.rdk_item.Delete()
    except Exception:
        pass
    print(f"Control 4")
    return item_final

def crear_bote_con_tapa_etiqueta_visual(bote_con_tapa, tipo):
    bote = bote_con_tapa
    tam = bote.dict_bote.get("tam", bote.dict_bote.get("tamano", "2L"))
    modelo_final = obtener_modelo_bote_etiqueta(tam)
    nombre_final = f"CBoteConEtiqueta_{bote.id_bote}"
    print(f"Control 1 - Modelo: {modelo_final}, Nombre final: {nombre_final}")

    if tipo == TipoBote.INTERIOR:
        ref_bote = REF_BOTE_CON_ETIQUETA_INT
        ref_cinta = REF_CINTA_INT
    else:
        ref_bote = REF_BOTE_CON_ETIQUETA_EXT
        ref_cinta = REF_CINTA_EXT

    print(f"  ref_bote={ref_bote}, ref_cinta={ref_cinta}")
    item_final = copiar_item(modelo_final, tam,  nombre_final, ref_nombre_static=ref_bote, ref_nombre_cinta=ref_cinta)
    if item_final is None or not item_final.Valid():
        print(f"[ERROR] No se pudo crear el item final para BoteConEtiqueta {bote.id_bote}")
        return None

    print(f"Control 2")
    try:
        bote.rdk_item.Delete() # Eliminas el BoteConTapa anterior despues de poner el bote con etiqueta
    except Exception as e:
        print(f"[ERROR] No se pudo eliminar bote: {e}")

    print(f"Control 3")
    return item_final
# ------------------------------------------------------------
# MQTT
# ------------------------------------------------------------

def handle_process(payload):
    try:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")

        bote_inf = json.loads(payload)
        cantidad = int(bote_inf.get("cantidad", 1))

        for _ in range(cantidad):
            encolar_pedidos(bote_inf.copy())

    except Exception as e:
        print(f"[ERROR] handle_process: {e}")


def encolar_pedidos(bote_inf: dict) -> int:
    with init.encolar_lock:
        try:
            tipo = str(bote_inf.get("tipo", "int")).lower()

            if tipo in ["int", "interior"]:
                bote_inf["tipo"] = "int"
                init.cola_general_int.put(bote_inf)
            else:
                bote_inf["tipo"] = "ext"
                init.cola_general_ext.put(bote_inf)

            return 0

        except Exception as e:
            print(f"[ERROR] encolar_pedidos: {e}")
            return 1


# ------------------------------------------------------------
# Generación
# ------------------------------------------------------------

def _encolar_sensor_dispensador(bote, tipo):
    if tipo == TipoBote.INTERIOR:
        init.cola_sensor_dispensador_int.put(bote)
    else:
        init.cola_sensor_dispensador_ext.put(bote)

def _generar_bote(bote_inf, tipo):
    with init.id_lock:
        init.id_bote_actual += 1
        init.id_tapa_actual += 1
        id_bote = init.id_bote_actual
        id_tapa = init.id_tapa_actual

    tam = normalizar_tamano(bote_inf.get("tam", bote_inf.get("tamano", "2L")))
    bote_inf["tam"] = tam
    bote_inf["tamano"] = tam

    modelo_bote = obtener_modelo_bote(tam)
    modelo_tapa = obtener_modelo_tapa(tam)

    if tipo == TipoBote.INTERIOR:
        ref_bote = REF_GEN_BOTE_INT
        ref_cinta = REF_CINTA_INT
        nombre_tipo = "int"
    else:
        ref_bote = REF_GEN_BOTE_EXT
        ref_cinta = REF_CINTA_EXT
        nombre_tipo = "ext"

    item_bote = copiar_item(
        modelo_bote,
        tam,
        f"CBote_{nombre_tipo}_{id_bote}",
        ref_nombre_static=ref_bote,
        ref_nombre_cinta=ref_cinta
    )

    bote = Bote(id_bote, bote_inf, item_bote)

    _encolar_sensor_dispensador(bote, tipo)

    if tipo == TipoBote.INTERIOR:
        init.cola_dispensador_int.put(bote)
    else:
        init.cola_dispensador_ext.put(bote)

    print(f"[GEN] Generado bote {id_bote} línea {nombre_tipo}, tamaño {tam}")

    return {
        "id_tapa": id_tapa,
        "modelo_tapa": modelo_tapa,
        "tam": tam,
        "tipo": tipo,
        "nombre_tipo": nombre_tipo
    }

def _generar_tapa(datos_tapa):
    with init.gen_tapas_lock:
        init.pedido_tapa_pendiente_generacion.set()

        while init.running:
            with init.cintas_lock:
                tapas_bloqueada = len(init.bloqueadores_cinta_tap) > 0
                cinta_tapas_parada = not init.cinta_tapas_running
                cinta_tapas_libre = len(init.bloqueadores_cinta_tap) == 0
                
            if cinta_tapas_parada and cinta_tapas_libre:
                break

            if tapas_bloqueada:
                print(f"[GEN TAPAS] Esperando cinta de tapas libre: {init.bloqueadores_cinta_tap}")
                time.sleep(0.05)
                continue

            print("[GEN TAPAS] Esperando parada válida de cinta de tapas...")
            init.cinta_tap_lista_para_generar.wait(timeout=0.1)

            if init.cinta_tap_lista_para_generar.is_set():
                init.cinta_tap_lista_para_generar.clear()
                break

        id_tapa = datos_tapa["id_tapa"]
        modelo_tapa = datos_tapa["modelo_tapa"]
        tam = datos_tapa["tam"]
        tipo = datos_tapa["tipo"]
        nombre_tipo = datos_tapa["nombre_tipo"]

        item_tapa = copiar_item(
            modelo_tapa,
            tam,
            f"CTapa_{nombre_tipo}_{id_tapa}",
            ref_nombre_static=REF_GEN_TAPA,
            ref_nombre_cinta=REF_CINTA_TAPAS
        )

        tapa = Tapa(id_tapa, tipo, item_tapa)

        init.cola_tapas.put(tapa)
        init.cola_sensor_tapas.put(tapa)

        init.global_tapas_generadas += 1

        if init.global_tapas_generadas == 5:
            init.numero_avisos_tapas += 1
            mqtt.manager.publish(
                TOPIC_TAPAS_PUB,
                json.dumps({"num_avisos": init.numero_avisos_tapas})
            )
            init.global_tapas_generadas = 0

        print(f"[GEN TAPAS] Generada tapa {id_tapa} línea {nombre_tipo}, tamaño {tam}")

        # Ya he generado la tapa pendiente
        init.pedido_tapa_pendiente_generacion.clear()

        with init.cintas_lock:
            if len(init.bloqueadores_cinta_tap) == 0:
                init.cinta_tapas_running = True

        # Aviso a mover_cinta_tapas()
        init.tapa_generada_event.set()

        time.sleep(0.2)

def generar_botes_int():
    primer_bote = True

    while init.running:
        bote_inf = init.cola_general_int.get()

        if bote_inf is None:
            time.sleep(0.2)
            continue

        init.pedido_int_pendiente_generacion.set()

        if primer_bote:
            primer_bote = False
        else:
            print("[GEN INT] Esperando parada válida de generación...")
            init.cinta_int_lista_para_generar.wait()
            init.cinta_int_lista_para_generar.clear()

        print("[GEN INT] Generando bote interior...")

        datos_tapa = _generar_bote(bote_inf, TipoBote.INTERIOR)

        mqtt.manager.publish(TOPIC_PROD_PUB, json.dumps({
            "numero_pedido": bote_inf.get("numero_pedido")
        }))

        init.pedido_int_pendiente_generacion.clear()

        # Liberar cinta interior ANTES de esperar/generar tapa
        with init.cintas_lock:
            if len(init.bloqueadores_cinta_int) == 0:
                init.cinta_interior_running = True

        init.bote_int_generado_event.set()

        print("[GEN INT] Bote interior generado y cinta liberada.")

        # Ahora sí, genero la tapa cuando la cinta de tapas esté libre
        _generar_tapa(datos_tapa)

        with init.cintas_lock:
            if len(init.bloqueadores_cinta_tap) == 0:
                init.cinta_tapas_running = True

def generar_botes_ext():
    primer_bote = True

    while init.running:
        bote_inf = init.cola_general_ext.get()

        if bote_inf is None:
            time.sleep(0.2)
            continue

        init.pedido_ext_pendiente_generacion.set()

        if primer_bote:
            primer_bote = False
        else:
            print("[GEN EXT] Esperando parada válida de generación...")
            init.cinta_ext_lista_para_generar.wait()
            init.cinta_ext_lista_para_generar.clear()

        print("[GEN EXT] Generando bote exterior...")

        datos_tapa = _generar_bote(bote_inf, TipoBote.EXTERIOR)

        mqtt.manager.publish(TOPIC_PROD_PUB, json.dumps({
            "numero_pedido": bote_inf.get("numero_pedido")
        }))

        init.pedido_ext_pendiente_generacion.clear()

        # Liberar cinta exterior ANTES de esperar/generar tapa
        with init.cintas_lock:
            if len(init.bloqueadores_cinta_ext) == 0:
                init.cinta_exterior_running = True

        init.bote_ext_generado_event.set()

        print("[GEN EXT] Bote exterior generado y cinta liberada.")

        # Ahora sí, genero la tapa cuando la cinta de tapas esté libre
        _generar_tapa(datos_tapa)

        with init.cintas_lock:
            if len(init.bloqueadores_cinta_tap) == 0:
                init.cinta_tapas_running = True


# ------------------------------------------------------------
# Dispensadores
# ------------------------------------------------------------

def dispensador_int():
    while init.running:
        init.sensor_dispensador_int.wait()
        init.sensor_dispensador_int.clear()
        if not init.running:
            break

        try:
            bote = init.cola_dispensador_int.get_nowait()
        except Empty:
            continue

        set_color_bote(bote)
        init.cola_esperar_tapa_int.put(bote)
        init.cola_sensor_poner_tapa_int.put(bote)

        init.reanudar_cinta_int("DISP_INT", "int")
        print(f"[DEBUG] CINTA INTERIOR PARADA")
        print(f"[DISP INT] Bote {bote.id_bote} coloreado y enviado a poner tapa")


def dispensador_ext():
    while init.running:
        init.sensor_dispensador_ext.wait()
        init.sensor_dispensador_ext.clear()
        if not init.running:
            break

        try:
            bote = init.cola_dispensador_ext.get_nowait()
        except Empty:
            continue

        set_color_bote(bote)
        init.cola_esperar_tapa_ext.put(bote)
        init.cola_sensor_poner_tapa_ext.put(bote)
        init.reanudar_cinta_ext("DISP_EXT", "ext")
        print(f"[DISP EXT] Bote {bote.id_bote} coloreado y enviado a poner tapa")


# ------------------------------------------------------------
# Tapas: cinta única global
# ------------------------------------------------------------

def colocar_tapas():
    botes_esperando = {
        TipoBote.INTERIOR: 0,
        TipoBote.EXTERIOR: 0
    }

    while init.running:
        init.sensor_tapas_final.wait()
        init.sensor_tapas_final.clear()

        if not init.running:
            break

        try:
            tapa = init.cola_tapas.get_nowait()
        except Empty:
            continue

        tipo_buscado = tapa.tipo  # El tipo de bote que necesita esta tapa física
        bote = None

        while init.running and bote is None:
            
            if botes_esperando[tipo_buscado] > 0:
                botes_esperando[tipo_buscado] -= 1
            else:
                try:
                    tipo_aviso = init.cola_auxiliar_sensor_tapas.get(timeout=0.1)
                    
                    if tipo_aviso != tipo_buscado:
                        botes_esperando[tipo_aviso] += 1
                        continue
                except Empty:
                    continue

            try:
                if tipo_buscado == TipoBote.INTERIOR:
                    bote = init.cola_esperar_tapa_int.get_nowait()
                else:
                    bote = init.cola_esperar_tapa_ext.get_nowait()
            except Empty:
                botes_esperando[tipo_buscado] += 1
                time.sleep(0.05)
                continue

        if not init.running or bote is None:
            break

        try:
            tap.pickandplace_tapa(tapa, bote, tipo_buscado)
        except Exception as e:
            print(f"[ERROR TAPAS] Falló pick and place de tapa: {e}")
            continue

        item_final = crear_bote_con_tapa_visual(bote, tapa, tipo_buscado)

        if item_final is None:
            print("[ERROR TAPAS] No se pudo crear bote con tapa visual")
            continue
        
        bote_con_tapa = BoteConTapa(bote.id_bote, tapa.id_tapa, bote.dict_bote, item_final)
        if tipo_buscado == TipoBote.INTERIOR:
            init.cola_etiquetadora_int.put(bote_con_tapa)
            init.cola_sensor_etiquetadora_int.put(bote_con_tapa)
            init.reanudar_cinta_int("TAPAS_INT", "int")
        else:
            init.cola_etiquetadora_ext.put(bote_con_tapa)
            init.cola_sensor_etiquetadora_ext.put(bote_con_tapa)
            init.reanudar_cinta_ext("TAPAS_EXT", "ext")

        print(f"[TAPAS] Tapa colocada correctamente en línea {tipo_buscado}")

        init.reanudar_cinta_tap("TAPAS")


# ------------------------------------------------------------
# Etiquetadoras
# ------------------------------------------------------------

def etiquetador_botes_int():
    while init.running:
        init.sensor_etiquetadora_int.wait()
        init.sensor_etiquetadora_int.clear()
        if not init.running:
            break
        try:
            bote_con_tapa = init.cola_etiquetadora_int.get_nowait()
        except Empty:
            continue

        print(f"Antes de crear bote + tapa")
        item_final = crear_bote_con_tapa_etiqueta_visual(bote_con_tapa, TipoBote.INTERIOR)
        print(f"Después de crear bote + tapa")
        
        # Validar que se creó correctamente el item
        if item_final is None:
            print(f"[ERROR ETIQ INT] No se pudo crear el item visual para BoteConTapa {bote_con_tapa.id_bote}/{bote_con_tapa.id_tapa}")
            continue
        
        bote_con_etiqueta = BoteConEtiqueta(bote_con_tapa.id_bote, bote_con_tapa.dict_bote, item_final)
        init.cola_agitadores_int.put(bote_con_etiqueta)
        init.cola_sensor_agitadores_int.put(bote_con_etiqueta)
        init.reanudar_cinta_int("ETIQ_INT", "int")
        print(f"[ETIQ INT] BoteConEtiqueta {bote_con_tapa.id_bote} creado")


def etiquetador_botes_ext():
    while init.running:
        init.sensor_etiquetadora_ext.wait()
        init.sensor_etiquetadora_ext.clear()
        if not init.running:
            break

        try:
            bote_con_tapa = init.cola_etiquetadora_ext.get_nowait()
        except Empty:
            continue

        item_final = crear_bote_con_tapa_etiqueta_visual(bote_con_tapa, TipoBote.EXTERIOR)
        
        # Validar que se creó correctamente el item
        if item_final is None:
            print(f"[ERROR ETIQ EXT] No se pudo crear el item visual para BoteConTapa {bote_con_tapa.id_bote}/{bote_con_tapa.id_tapa}")
            continue
        
        bote_con_etiqueta = BoteConEtiqueta(bote_con_tapa.id_bote, bote_con_tapa.dict_bote, item_final)
        init.cola_agitadores_ext.put(bote_con_etiqueta)
        init.cola_sensor_agitadores_ext.put(bote_con_etiqueta)
        init.reanudar_cinta_ext("ETIQ_EXT", "ext")
        print(f"[ETIQ EXT] BoteConEtiqueta {bote_con_tapa.id_bote} creado")


# ------------------------------------------------------------
# Agitadores
# ------------------------------------------------------------

def _buscar_agitador_libre(tipo):
    with init.agitadores_lock:
        if tipo == TipoBote.INTERIOR:
            if init.estado_agitador_der_int == estadoAgitador.LIBRE:
                init.estado_agitador_der_int = estadoAgitador.OCUPADO
                return Agitador.DER_INT
            if init.estado_agitador_izq_int == estadoAgitador.LIBRE:
                init.estado_agitador_izq_int = estadoAgitador.OCUPADO
                return Agitador.IZQ_INT
        else:
            if init.estado_agitador_der_ext == estadoAgitador.LIBRE:
                init.estado_agitador_der_ext = estadoAgitador.OCUPADO
                return Agitador.DER_EXT
            if init.estado_agitador_izq_ext == estadoAgitador.LIBRE:
                init.estado_agitador_izq_ext = estadoAgitador.OCUPADO
                return Agitador.IZQ_EXT
    return None


def _liberar_agitador(agitador):
    with init.agitadores_lock:
        if agitador == Agitador.DER_INT:
            init.estado_agitador_der_int = estadoAgitador.LIBRE
        elif agitador == Agitador.IZQ_INT:
            init.estado_agitador_izq_int = estadoAgitador.LIBRE
        elif agitador == Agitador.DER_EXT:
            init.estado_agitador_der_ext = estadoAgitador.LIBRE
        elif agitador == Agitador.IZQ_EXT:
            init.estado_agitador_izq_ext = estadoAgitador.LIBRE


def poner_agitadores_int():
    while init.running:
        init.sensor_agitadores_int.wait()
        init.sensor_agitadores_int.clear()
        if not init.running:
            break

        agitador = None
        while init.running and agitador is None:
            agitador = _buscar_agitador_libre(TipoBote.INTERIOR)
            if agitador is None:
                time.sleep(0.25)

        try:
            bote_con_tapa = init.cola_agitadores_int.get_nowait()
        except Empty:
            _liberar_agitador(agitador)
            continue

        agi.meter_bote(bote_con_tapa, bote_con_tapa.tipo, agitador)
        init.reanudar_cinta_int("AGI_INT", "int")

        segundos = random.randint(6, 15)
        init.cola_proceso_agitador_int.put((bote_con_tapa, agitador, segundos))
        print(f"[AGI INT] Bote {bote_con_tapa.id_bote} en {agitador} durante {segundos}s")


def poner_agitadores_ext():
    while init.running:
        init.sensor_agitadores_ext.wait()
        init.sensor_agitadores_ext.clear()
        if not init.running:
            break

        agitador = None
        while init.running and agitador is None:
            agitador = _buscar_agitador_libre(TipoBote.EXTERIOR)
            if agitador is None:
                time.sleep(0.25)

        try:
            bote_con_tapa = init.cola_agitadores_ext.get_nowait()
        except Empty:
            _liberar_agitador(agitador)
            continue

        agi.meter_bote(bote_con_tapa, bote_con_tapa.tipo, agitador)
        init.reanudar_cinta_ext("AGI_EXT", "ext")

        segundos = random.randint(6, 15)
        init.cola_proceso_agitador_ext.put((bote_con_tapa, agitador, segundos))
        print(f"[AGI EXT] Bote {bote_con_tapa.id_bote} en {agitador} durante {segundos}s")


def esperar_agitacion_int():
    while init.running:
        try:
            bote_con_tapa, agitador, segundos = init.cola_proceso_agitador_int.get(timeout=0.2)
        except Empty:
            continue
        time.sleep(segundos)
        init.cola_salida_agitador_int.put((bote_con_tapa, agitador))
        print(f"[AGI INT] Bote {bote_con_tapa.id_bote} terminado en {agitador}")


def esperar_agitacion_ext():
    while init.running:
        try:
            bote_con_tapa, agitador, segundos = init.cola_proceso_agitador_ext.get(timeout=0.2)
        except Empty:
            continue
        time.sleep(segundos)
        init.cola_salida_agitador_ext.put((bote_con_tapa, agitador))
        print(f"[AGI EXT] Bote {bote_con_tapa.id_bote} terminado en {agitador}")


def sacar_botes_agitados_int():
    while init.running:
        try:
            bote_con_tapa, agitador = init.cola_salida_agitador_int.get(timeout=0.5)
        except Empty:
            continue

        while True:
            with init.estado_pedestal_int_lock:
                if init.estado_pedestal_paletizado_int:
                    break
            print(f"[PEDESTAL INT] Esperando pedestal libre para sacar bote {bote_con_tapa.id_bote} del agitador...")
            time.sleep(0.2)
        try:
            agi.sacar_bote(bote_con_tapa, bote_con_tapa.tipo, agitador)
        except Exception as e:
            print(f"[ERROR] sacar agitador falló: {e}")

        init.cola_paletizado_int.put(bote_con_tapa)
        init.cola_sensor_paletizado_int.put(bote_con_tapa)
        with init.estado_pedestal_int_lock:
            init.estado_pedestal_paletizado_int = False # Ocupo el pedestal hasta que se paletice el bote, no dejo que otro bote salga del agitador para no bloquear el hilo de procesos
            print(f"[PEDESTAL INT] Pedestal ocupado para bote {bote_con_tapa.id_bote} del agitador {agitador}")
        _liberar_agitador(agitador)

        print(f"[SALIDA AGI INT] Bote {bote_con_tapa.id_bote} a paletizado")


def sacar_botes_agitados_ext():
    while init.running:
        try:
            bote_con_tapa, agitador = init.cola_salida_agitador_ext.get(timeout=0.5)
        except Empty:
            continue
        while True:
            with init.estado_pedestal_ext_lock:
                if init.estado_pedestal_paletizado_ext:
                    break
            print(f"[PEDESTAL EXT] Esperando pedestal libre para sacar bote {bote_con_tapa.id_bote} del agitador...")
            time.sleep(0.2)
        try:
            agi.sacar_bote(bote_con_tapa, bote_con_tapa.tipo, agitador)
        except Exception as e:
            print(f"[ERROR] sacar agitador falló: {e}")
        with init.estado_pedestal_ext_lock:
            init.estado_pedestal_paletizado_ext = False # Ocupo el pedestal hasta que se paletice el bote, no dejo que otro bote salga del agitador para no bloquear el hilo de procesos
            print(f"[PEDESTAL EXT] Pedestal ocupado para bote {bote_con_tapa.id_bote} del agitador {agitador}")
        init.cola_paletizado_ext.put(bote_con_tapa)
        init.cola_sensor_paletizado_ext.put(bote_con_tapa)
        _liberar_agitador(agitador)
        print(f"[SALIDA AGI EXT] Bote {bote_con_tapa.id_bote} a paletizado")


# ------------------------------------------------------------
# Paletizado
# ------------------------------------------------------------

def paletizado_int():
    while init.running:
        init.sensor_paletizado_int.wait()
        init.sensor_paletizado_int.clear()
        if not init.running:
            break

        try:
            bote_con_tapa = init.cola_paletizado_int.get_nowait()
        except Empty:
            continue
        mqtt.manager.publish(TOPIC_FINALIZADO_PUB, json.dumps({"numero_pedido": bote_con_tapa.dict_bote.get("numero_pedido")}))
        try:
            pal.pick_pedestal_int(bote_con_tapa) # Primero lo llevo al pedestal para que no bloquee el hilo de sacar_botes_agitados_int mientras se paletiza el bote, así otro bote puede salir del agitador y esperar en el pedestal mientras se paletiza el primer bote
        except Exception as e:
            print(f"[ERROR] pick_pedestal_int falló: {e}")
        try:
            pal.paletizar_bote(bote_con_tapa)
        except Exception as e:
            print(f"[ERROR] paletizado falló: {e}")
        with init.estado_pedestal_int_lock:
            init.estado_pedestal_paletizado_int = True # Libero el pedestal para que se pueda sacar otro bote del agitador, no dejo que otro bote salga del agitador para no bloquear el hilo de procesos
            print(f"[PEDESTAL INT] Pedestal libre después de paletizar bote {bote_con_tapa.id_bote}")
        print(f"[PAL INT] Bote {bote_con_tapa.id_bote} paletizado")


def paletizado_ext():
    while init.running:
        init.sensor_paletizado_ext.wait()
        init.sensor_paletizado_ext.clear()
        if not init.running:
            break

        try:
            bote_con_tapa = init.cola_paletizado_ext.get_nowait()
        except Empty:
            continue
        mqtt.manager.publish(TOPIC_FINALIZADO_PUB, json.dumps({"numero_pedido": bote_con_tapa.dict_bote.get("numero_pedido")}))
        try:
            pal.pick_pedestal_ext(bote_con_tapa) # Primero lo llevo al pedestal para que no bloquee el hilo de sacar_botes_agitados_ext mientras se paletiza el bote, así otro bote puede salir del agitador y esperar en el pedestal mientras se paletiza el primer bote
        except Exception as e:
            print(f"[ERROR] pick_pedestal_ext falló: {e}")
        try:
            pal.paletizar_bote(bote_con_tapa)
        except Exception as e:
            print(f"[ERROR] paletizado falló: {e}")
            
        with init.estado_pedestal_ext_lock:
            init.estado_pedestal_paletizado_ext = True # Libero el pedestal para que se pueda sacar otro bote del agitador, no dejo que otro bote salga del agitador para no bloquear el hilo de procesos
            print(f"[PEDESTAL EXT] Pedestal libre después de paletizar bote {bote_con_tapa.id_bote}")
        print(f"[PAL EXT] Bote {bote_con_tapa.id_bote} paletizado")