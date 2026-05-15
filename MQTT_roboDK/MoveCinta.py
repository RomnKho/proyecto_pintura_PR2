import time
from robodk.robomath import *
from robodk.robolink import *
import Init

incremento = 300

# ------- TAREAS DE MOVER CINTA, GENERAR Y PINTAR BOTES / TAPAS --------

# Thread de la cinta ya que se tiene que mover independientemente de si hay pedidos nuevos o no
def mueve_cinta_interior():

    RDK_hilo_cinta = Robolink()

    cinta_interior = RDK_hilo_cinta.Item("[INTERIOR] CintaMovil")
    set_flag_int = False

    if cinta_interior.Valid():
        while 1:
            if not Init.stop_interior:

                # Si no hay pedidos, no puedo setear el flag asi como asi
                with Init.mutex_pedido_interior:
                    if Init.botes_int_restantes > 0:
                        set_flag_int = True
                    else:
                        set_flag_int = False

                cinta_interior.MoveJ(cinta_interior.Joints() + incremento)

                if set_flag_int:
                    Init.cola_sinc_spawn_interior.set()       # Pone el flag a true

            time.sleep(1) # Tiempo por dispensador
# -------------------------------------------------------------------------------------------------------------

# Thread de la cinta ya que se tiene que mover independientemente de si hay pedidos nuevos o no
def mueve_cinta_exterior():

    RDK_hilo_cinta = Robolink()

    cinta_exterior = RDK_hilo_cinta.Item("[EXTERIOR] CintaMovil")
    set_flag_ext = False

    if not(cinta_exterior.Valid()):
        RDK_hilo_cinta.ShowMessage("Cinta externa no es valid")
        return

    while 1:
        if not Init.stop_exterior:

            with Init.mutex_pedido_exterior:
                if Init.botes_ext_restantes > 0:
                    set_flag_ext = True
                else:
                    set_flag_ext = False
            
            cinta_exterior.MoveJ(cinta_exterior.Joints() + incremento)

            if set_flag_ext:
                Init.cola_sinc_spawn_exterior.set()       # Pone el flag a true

        time.sleep(1)
                                
# -------------------------------------------------------------------------------------------------------------

# Thread que mueve la cinta de las tapas
def mueve_cinta_tapas():

    RDK_hilo_cinta = Robolink()

    cinta_tapas = RDK_hilo_cinta.Item("[TAPAS] CintaMovil")
    set_flag = False

    if cinta_tapas.Valid():
        while 1:
            if not Init.stop_tapas: # Se para si el sensor lee que hay un bote al final de la cinta

                with Init.mutex_pedido_tapas:
                    if Init.tapas_restantes > 0:
                        set_flag = True
                    else:
                        set_flag = False

                cinta_tapas.MoveJ(cinta_tapas.Joints() + incremento)

                if set_flag:
                    if cinta_tapas.Joints().rows[0][0] % 300 == 0:
                        Init.cola_sinc_spawn_tapas.set()

                time.sleep(1)
            else:
                time.sleep(0.2)

# -------------------------------------------------------------------------------------------------------------

# Thread que lee si hay algo en la cola y manda a generar bote en la cinta interior
def generar_bote_interior():

    RDK_hilo_interior = Robolink()

    # DEFINICIÓN DE OBJETOS
    frame_cinta = RDK_hilo_interior.Item("[INTERIOR] FrameCinta", ITEM_TYPE_FRAME)
    frame_color = RDK_hilo_interior.Item("[INTERIOR] FrameColor", ITEM_TYPE_FRAME)
    frame_static = RDK_hilo_interior.Item("[INTERIOR] StaticFrameCinta", ITEM_TYPE_FRAME)
    sensor_place = RDK_hilo_interior.Item("[INTERIOR] SensorBotes")

    botes_parar = []

    if frame_cinta.Valid() and frame_color.Valid() and frame_static.Valid():
        # MOVER LA CINTA Y MULTIPLICAR LOS BOTES
        while 1:
            # Miro si ha colisionado el bote con el sensor
            while Init.cola_info_pedido_interior.empty():
                if botes_parar:
                    if sensor_place.Collision(botes_parar[0]):
                        # Parar cinta
                        Init.stop_interior = True
                        # Mandar okei a scara
                        Init.cola_sinc_scara_interior.set()
                        # Scara decide cuanto retomar
                        botes_parar.pop(0)
                time.sleep(0.5)

            # Recojo de la cola => Si no hay objetos se queda esperando
            info_bote = Init.cola_info_pedido_interior.get()

            rgb = info_bote.rgb_hex
            tam = info_bote.tamano
            cantidad = info_bote.cantidad

            bote_pintura_obj = RDK_hilo_interior.Item(f"[TEMPORAL] BotePintura{tam}", ITEM_TYPE_OBJECT)

            # Se repite el proceso de copiado-pegado tantas veces como botes hayan sido pedidos
            for _ in range(int(cantidad)):
                # Miro si ha colisionado el bote con el sensor
                if botes_parar:
                    if sensor_place.Collision(botes_parar[0]):
                        # Parar cinta
                        Init.stop_interior = True
                        # Mandar okei a scara
                        Init.cola_sinc_scara_interior.set()
                        # Scara decide cuanto retomar
                        botes_parar.pop(0)

                Init.cola_sinc_spawn_interior.wait()      # Sincronizacion con hilo de cinta
                Init.cola_sinc_spawn_interior.clear()     # Pone el flag a false

                with Init.mutex_portapapeles:             # Mutex para evitar la sobrescritura del copy-paste
                    bote_pintura_obj.Copy()               # Copio el bote del tamaño que es
                    bote_pintura_copy = RDK_hilo_interior.Paste(frame_static)

                with Init.mutex_num_pedido:
                    bote_pintura_copy.setName(f"Bote{tam}_{Init.num_pedido}")
                    Init.num_pedido += 1

                bote_pintura_copy.setParentStatic(frame_cinta)
                Init.cola_bote_a_pintar_interior.put({"item":bote_pintura_copy, "tam":tam})
                Init.cola_colores_interior.put(rgb)                        # Añado el color a pintar

                partes_bote = bote_pintura_copy.Childs()
                bote_nombre = f"BotePintura{tam}_bote"  # Busco al child

                for i in range(3):              # Distingo el bote propio del objeto en si
                    if bote_nombre in partes_bote[i].Name():
                        bote = partes_bote[i]
                        break

                botes_parar.append(bote) # !!!

                # Disminuyo el contador de botes restantes
                with Init.mutex_pedido_interior:
                    if Init.botes_int_restantes > 0:
                        Init.botes_int_restantes -= 1

                time.sleep(0.2)

            time.sleep(0.5)

# -------------------------------------------------------------------------------------------------------------

# Thread que lee si hay algo en la cola y manda a generar bote en la cinta exterior
def generar_bote_exterior():

    RDK_hilo_exterior = Robolink()

    # DEFINICIÓN DE OBJETOS
    frame_cinta = RDK_hilo_exterior.Item("[EXTERIOR] FrameCinta", ITEM_TYPE_FRAME)
    frame_color = RDK_hilo_exterior.Item("[EXTERIOR] FrameColor", ITEM_TYPE_FRAME)
    frame_static = RDK_hilo_exterior.Item("[EXTERIOR] StaticFrameCinta", ITEM_TYPE_FRAME)
    sensor_place = RDK_hilo_exterior.Item("[EXTERIOR] SensorBotes")

    botes_parar = []

    if frame_cinta.Valid() and frame_color.Valid() and frame_static.Valid() and sensor_place.Valid():
        # MOVER LA CINTA Y MULTIPLICAR LOS BOTES
        while 1:
            while Init.cola_info_pedido_exterior.empty():
                if botes_parar:
                    if sensor_place.Collision(botes_parar[0]):
                        # Parar cinta
                        Init.stop_exterior = True
                        # Mandar okei a scara
                        Init.cola_sinc_scara_exterior.set()
                        # Scara decide cuanto retomar
                        botes_parar.pop(0)
                time.sleep(0.5)

            # Recojo de la cola => Si no hay objetos se queda esperando
            info_bote = Init.cola_info_pedido_exterior.get()

            rgb = info_bote.rgb_hex
            tam = info_bote.tamano
            cantidad = info_bote.cantidad

            bote_pintura_obj = RDK_hilo_exterior.Item(f"[TEMPORAL] BotePintura{tam}", ITEM_TYPE_OBJECT)

            # Se repite el proceso de copiado-pegado tantas veces como botes hayan sido pedidos
            for _ in range(int(cantidad)):

                if botes_parar:
                    if sensor_place.Collision(botes_parar[0]):
                        # Parar cinta
                        Init.stop_exterior = True
                        # Mandar okei a scara
                        Init.cola_sinc_scara_exterior.set()
                        # Scara decide cuanto retomar
                        botes_parar.pop(0)

                Init.cola_sinc_spawn_exterior.wait()      # Sincronizacion con hilo de cinta
                Init.cola_sinc_spawn_exterior.clear()     # Pone el flag a false

                with Init.mutex_portapapeles:             # Mutex para evitar la sobrescritura del copy-paste
                    bote_pintura_obj.Copy()               # Copio el bote del tamaño que es
                    bote_pintura_copy = RDK_hilo_exterior.Paste(frame_static)

                with Init.mutex_num_pedido:
                    bote_pintura_copy.setName(f"Bote{tam}_{Init.num_pedido}")
                    Init.num_pedido += 1
                
                bote_pintura_copy.setParentStatic(frame_cinta)
                Init.cola_bote_a_pintar_exterior.put({"item":bote_pintura_copy, "tam":tam})
                Init.cola_colores_exterior.put(rgb)                        # Añado el color a pintar

                partes_bote = bote_pintura_copy.Childs()
                bote_nombre = f"BotePintura{tam}_bote"  # Busco al child

                for i in range(3):              # Distingo el bote propio del objeto en si
                    if bote_nombre in partes_bote[i].Name():
                        bote = partes_bote[i]
                        break

                botes_parar.append(bote) # !!!

                # Disminuyo el contador de botes restantes
                with Init.mutex_pedido_exterior:
                    if Init.botes_ext_restantes > 0:
                        Init.botes_ext_restantes -= 1
                 
                time.sleep(0.2)

            time.sleep(0.5)

# -------------------------------------------------------------------------------------------------------------

# Thread que lee si hay algo en la cola y manda a generar tapas
def generar_tapas():
    RDK_tapas = Robolink()
    
    # Objetos necesarios
    frame_tapas = RDK_tapas.Item("[TAPAS] FrameCinta", ITEM_TYPE_FRAME)
    frame_static = RDK_tapas.Item("[TAPAS] FrameStatic", ITEM_TYPE_FRAME)
    sensor_tapas = RDK_tapas.Item("[TAPAS] Sensor")

    # Contadores locales para saber cuántas tapas faltan por generar de cada pedido actual
    pendientes_int = 0
    tam_int = ""
    pendientes_ext = 0
    tam_ext = ""
    num_tapas = 0

    # Vector local que identifica el primero de la fila de tapas
    tapas_parar_v = []

    if not(frame_tapas.Valid() and sensor_tapas.Valid() and frame_static.Valid()):
        RDK_tapas.ShowMessage("Algo no es valido en generar_tapas")

    while True:
        # Intentar capturar nuevos pedidos si no hay nada pendiente
        if pendientes_int == 0 and not Init.cola_info_pedido_interior_tapas.empty():
            pedido = Init.cola_info_pedido_interior_tapas.get()
            pendientes_int = int(pedido.cantidad)
            tam_int = pedido.tamano
            tapa_int = RDK_tapas.Item(f"Tapa{tam_int}", ITEM_TYPE_OBJECT)

        if pendientes_ext == 0 and not Init.cola_info_pedido_exterior_tapas.empty():
            pedido = Init.cola_info_pedido_exterior_tapas.get()
            pendientes_ext = int(pedido.cantidad)
            tam_ext = pedido.tamano
            tapa_ext = RDK_tapas.Item(f"Tapa{tam_ext}", ITEM_TYPE_OBJECT)

        # Miro si ha chocado una tapa de interior con el sesnor
        if pendientes_ext > 0:
            Init.cola_sinc_spawn_tapas.wait()
            Init.cola_sinc_spawn_tapas.clear()

            while Init.stop_tapas:
                time.sleep(0.2)
            
            with Init.mutex_portapapeles:    # Mutex para evitar la sobrescritura del copy-paste
                tapa_ext.Copy()
                tapa_copy = RDK_tapas.Paste(frame_static)

            tapa_copy.setParentStatic(frame_tapas)
            tapa_copy.setName(f"Tapa{tam_ext}_{num_tapas}")
            num_tapas += 1

            # Meto en la cola local
            tapas_parar_v.append({"item":tapa_copy, "linea": "Ext", "tam": tam_ext, "num_tapa": num_tapas})
            pendientes_ext -= 1

            with Init.mutex_pedido_tapas:
                if Init.tapas_restantes > 0:
                    Init.tapas_restantes -= 1

            time.sleep(0.5)

        if tapas_parar_v:
            # Miro si ha chocado una tapa con el sensor
            if sensor_tapas.Collision(tapas_parar_v[0]["item"]):
                Init.stop_tapas = True
                # Meter en la cola para que el SCARA sepa qué coger
                Init.cola_scara.put({"item": tapas_parar_v[0]["item"], "linea": tapas_parar_v[0]["linea"], "tam": tapas_parar_v[0]["tam"], "num_tapa": tapas_parar_v[0]["num_tapa"]})
                tapas_parar_v.pop(0)

        # Generar una tapa de Interior (si toca)
        if pendientes_int > 0:

            # Esperar sincronización de hueco en cinta de tapas
            Init.cola_sinc_spawn_tapas.wait()
            Init.cola_sinc_spawn_tapas.clear()

            while Init.stop_tapas:
                time.sleep(0.2)

            with Init.mutex_portapapeles:
                tapa_int.Copy()
                tapa_copy = RDK_tapas.Paste(frame_static)

            tapa_copy.setParentStatic(frame_tapas)
            tapa_copy.setName(f"Tapa{tam_int}_{num_tapas}")
            num_tapas += 1
            # Meto en la cola local
            tapas_parar_v.append({"item":tapa_copy, "linea": "Int", "tam": tam_int, "num_tapa": num_tapas})
            pendientes_int -= 1

            with Init.mutex_pedido_tapas:
                if Init.tapas_restantes > 0:
                    Init.tapas_restantes -= 1

            time.sleep(0.5)

        if tapas_parar_v:
            # Miro si ha chocado una tapa con el sensor
            if sensor_tapas.Collision(tapas_parar_v[0]["item"]):
                Init.stop_tapas = True
                # Meter en la cola para que el SCARA sepa qué coger
                Init.cola_scara.put({"item": tapas_parar_v[0]["item"], "linea": tapas_parar_v[0]["linea"], "tam": tapas_parar_v[0]["tam"], "num_tapa": tapas_parar_v[0]["num_tapa"]})
                tapas_parar_v.pop(0)
          
        # Si no hay nada en ninguna cola, esperamos un poco
        if pendientes_int == 0 and pendientes_ext == 0:
            time.sleep(0.5)

# -------------------------------------------------------------------------------------------------------------

# Thread que pinta los botes al final de los dispensadores de la cinta interior
def pintar_bote_interior():

    RDK_hilo_pintado_interior = Robolink()

    cinta = RDK_hilo_pintado_interior.Item("[INTERIOR] CintaMovil")
    sensor = RDK_hilo_pintado_interior.Item("[INTERIOR] SensorColor")

    if cinta.Valid() and sensor.Valid():

        while 1:

            bote_info = Init.cola_bote_a_pintar_interior.get()
            bote_entero = bote_info["item"]
            partes_bote = bote_entero.Childs()
            tam = bote_info["tam"]
            pintura_nombre = f"BotePintura{tam}_pintura"
            bote_nombre = f"BotePintura{tam}_bote"

            for i in range(3):
                if bote_nombre in partes_bote[i].Name():
                    bote = partes_bote[i]
                    break

            if bote is None:
                bote = RDK_hilo_pintado_interior.Item(bote_nombre)

            while not sensor.Collision(bote):
                time.sleep(0.5)

            for i in range(3):
                if pintura_nombre in partes_bote[i].Name():
                    pintura = partes_bote[i]
                    break
                
            if pintura is None:
                    pintura = RDK_hilo_pintado_interior.Item(pintura_nombre)

            rgb = Init.cola_colores_interior.get()

            # DESCOMPOSICION DEL RGB
            r_hex = rgb[0:2]
            g_hex = rgb[2:4]
            b_hex = rgb[4:6]

            r = int(r_hex, 16) / 255
            g = int(g_hex, 16) / 255
            b = int(b_hex, 16) / 255

            pintura.setColor([r,g,b,1])

            time.sleep(0.5)

# -------------------------------------------------------------------------------------------------------------

# Thread que pinta los botes al final de los dispensadores de la cinta interior
def pintar_bote_exterior():

    RDK_hilo_pintado_exterior = Robolink()

    cinta = RDK_hilo_pintado_exterior.Item("[EXTERIOR] CintaMovil")
    sensor = RDK_hilo_pintado_exterior.Item("[EXTERIOR] SensorColor")

    if cinta.Valid() and sensor.Valid():
        while 1:

            bote_info = Init.cola_bote_a_pintar_exterior.get()
            bote = bote_info["item"]
            partes_bote = bote.Childs()
            tam = bote_info["tam"]
            pintura_nombre = f"BotePintura{tam}_pintura"
            bote_nombre = f"BotePintura{tam}_bote"

            for i in range(3):
                if bote_nombre in partes_bote[i].Name():
                    bote = partes_bote[i]
                    break
            
            if bote is None:
                bote = RDK_hilo_pintado_exterior.Item(bote_nombre)

            while not sensor.Collision(bote):
                time.sleep(0.5)

            for i in range(3):
                if pintura_nombre in partes_bote[i].Name():
                    pintura = partes_bote[i]
                    break
                
            if pintura is None:
                    pintura = RDK_hilo_pintado_exterior.Item(pintura_nombre)

            rgb = Init.cola_colores_exterior.get()

            # DESCOMPOSICION DEL RGB
            r_hex = rgb[0:2]
            g_hex = rgb[2:4]
            b_hex = rgb[4:6]

            r = int(r_hex, 16) / 255
            g = int(g_hex, 16) / 255
            b = int(b_hex, 16) / 255

            pintura.setColor([r,g,b,1])

            time.sleep(0.5)

# -------------------------------------------------------------------------------------------------------------