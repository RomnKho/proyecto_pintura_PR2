
from robodk.robomath import *
from robodk.robolink import *
import time
import Init

incremento = 300

# ------- TAREAS DE MOVER CINTA Y GENERAR BOTES --

# Thread de la cinta ya que se tiene que mover independientemente de si hay pedidos nuevos o no
def mueve_cinta():

    RDK_hilo_cinta = Robolink()

    cinta_interior = RDK_hilo_cinta.Item("[INTERIOR] CintaMovil")
    cinta_exterior = RDK_hilo_cinta.Item("[EXTERIOR] CintaMovil")

    if cinta_interior.Valid() and cinta_exterior.Valid():
        while 1:
            cinta_interior.MoveJ(cinta_interior.Joints() + incremento)
            time.sleep(1) # Tiempo por dispensador
            cinta_exterior.MoveJ(cinta_exterior.Joints() + incremento)
            time.sleep(1) # Desincronizacion de las cintas para que al Scara le de tiempo de poner la tapa

# -------------------------------------------------------------------------------------------------------------

# Thread que lee si hay algo en la cola y manda a generar bote en la cinta interior
def generar_bote_interior():

    RDK_hilo_interior = Robolink()

    # DEFINICIÓN DE OBJETOS
    frame_cinta = RDK_hilo_interior.Item("[INTERIOR] FrameCinta", ITEM_TYPE_FRAME)
    bote_pintura_obj = RDK_hilo_interior.Item("[INTERIOR] Bote_pintura", ITEM_TYPE_OBJECT)

    Init.cola_bote_pintura_interior.put(bote_pintura_obj) # Añado el primer cubo
    Init.cola_bote_a_pintar_interior.put(bote_pintura_obj) # Añado el primer cubo

    primer_pedido = True
    num_copia = 0

    if bote_pintura_obj.Valid() and frame_cinta.Valid():
        # MOVER LA CINTA Y MULTIPLICAR LOS BOTES
        while 1:
            # Recojo de la cola => Si no hay objetos se queda esperando
            info_bote = Init.cola_info_pedido_interior.get()

            rgb = info_bote.rgb_hex
            tam = info_bote.tamano
            cantidad = info_bote.cantidad

            # Se repite el proceso de copiado-pegado tantas veces como botes hayan sido pedidos
            for i in range(0, int(cantidad)):

                # Si es el primer pedido solo se hace visible el primer objeto
                if primer_pedido == True:
                    bote_pintura_obj.Childs()[0].setVisible(True)
                    bote_pintura_obj.Childs()[1].setVisible(True)
                    bote_pintura_obj.Childs()[2].setVisible(True)
                    primer_pedido = False

                # Si no es el primer pedido hay que hacer copias 
                else:
                    ultimo_bote = Init.cola_bote_pintura_interior.get()
                    ultimo_bote.Copy()                                       # Copio el ultimo bote añadido a la cola
                    bote_pintura_copy = RDK_hilo_interior.Paste(frame_cinta)
                    bote_pintura_copy.setName(f"[INTERIOR] Bote_pintura_{num_copia}")
                    num_copia += 1
                    Init.cola_bote_pintura_interior.put(bote_pintura_copy)   # Añado el siguiente bote
                    Init.cola_bote_a_pintar_interior.put(bote_pintura_copy)

                    # Traslación del bote pegado              
                    bote_pintura_copy.setPose(ultimo_bote.Pose() * robomath.transl(-incremento, 0, 0))
                
                Init.cola_colores_interior.put(rgb)                      # Añado el color a pintar
                time.sleep(0.2)
            
            time.sleep(0.5)

# -------------------------------------------------------------------------------------------------------------

# Thread que lee si hay algo en la cola y manda a generar bote en la cinta exterior
def generar_bote_exterior():

    RDK_hilo_exterior = Robolink()
    # DEFINCION DE OBJETOS
    cinta = RDK_hilo_exterior.Item("[EXTERIOR] CintaMovil")
    frame_cinta = RDK_hilo_exterior.Item("[EXTERIOR] FrameCinta", ITEM_TYPE_FRAME)
    bote_pintura_obj = RDK_hilo_exterior.Item("[EXTERIOR] Bote_pintura", ITEM_TYPE_OBJECT)
    pintura_nombre = "[EXTERIOR] Pintura"

    Init.cola_bote_pintura_exterior.put(bote_pintura_obj) # Añado el primer cubo
    Init.cola_bote_a_pintar_exterior.put(bote_pintura_obj) # Añado el primer cubo

    primer_pedido = True

    if cinta.Valid() and bote_pintura_obj.Valid() and frame_cinta.Valid():
        # MOVER LA CINTA Y MULTIPLICAR LOS BOTES
        while 1:
            # Recojo de la cola => Si no hay objetos se queda esperando¿?
            info_bote = Init.cola_info_pedido_exterior.get()
            RDK_hilo_exterior.ShowMessage("Voy a hacer un pedido en exterior")

            rgb = info_bote.rgb_hex
            tam = info_bote.tamano
            cantidad = info_bote.cantidad

            # DESCOMPOSICION DEL RGB
            r_hex = rgb[0:2]
            g_hex = rgb[2:4]
            b_hex = rgb[4:6]

            r = int(r_hex, 16) / 255
            g = int(g_hex, 16) / 255
            b = int(b_hex, 16) / 255

            RDK_hilo_exterior.ShowMessage(f"r: {r}, g: {g}, b: {b}")

            # Se repite el proceso de copiado-pegado tantas veces como botes hayan sido pedidos
            for i in range(0, int(cantidad)):

                # Si es el primer pedido solo se hace visible el primer objeto
                if primer_pedido == True:
                    bote_pintura_obj.Childs()[0].setVisible(True)
                    bote_pintura_obj.Childs()[1].setVisible(True)
                    bote_pintura_obj.Childs()[2].setVisible(True)
                    primer_pedido = False

                # Si no es el primer pedido hay que hacer copias 
                else:
                    ultimo_bote = Init.cola_bote_pintura_exterior.get()
                    ultimo_bote.Copy()                              # Copio el ultimo bote añadido a la cola
                    bote_pintura_copy = RDK_hilo_exterior.Paste(frame_cinta) 
                    Init.cola_bote_pintura_exterior.put(bote_pintura_copy)   # Añado el siguiente bote
                    Init.cola_bote_a_pintar_exterior.put(bote_pintura_copy)

                    # Traslación del bote pegado              
                    bote_pintura_copy.setPose(ultimo_bote.Pose() * robomath.transl(-incremento, 0, 0))

                x_bote = cinta.Joints().rows[0][0]

                # En x = 900 esta el ultimo dispensador
                if x_bote >= 900:
                    partes_bote = Init.cola_bote_a_pintar_exterior.get().Childs()

                    for i in range(1,3):
                        if pintura_nombre in partes_bote[i].Name():
                            pintura = partes_bote[i]
                            break
                        else:
                            pintura = RDK_hilo_exterior.Item(pintura_nombre)

                    pintura.setColor([r,g,b,1])

                time.sleep(0.2)
            
            time.sleep(0.5)

# -------------------------------------------------------------------------------------------------------------

# Thread que pinta los botes al final de los dispensadores de la cinta interior
def pintar_bote_interior():

    RDK_hilo_pintado_interior = Robolink()

    cinta = RDK_hilo_pintado_interior.Item("[INTERIOR] CintaMovil")
    pintura_nombre = "[INTERIOR] Pintura"

    if cinta.Valid():

        while 1:

            x_bote = cinta.Joints().rows[0][0]

            # En x = 900 esta el ultimo dispensador
            if x_bote >= 900 and not Init.cola_bote_a_pintar_interior.empty() and not Init.cola_colores_interior.empty():

                RDK_hilo_pintado_interior.ShowMessage("He entrado al if")

                bote = Init.cola_bote_a_pintar_interior.get()
                RDK_hilo_pintado_interior.ShowMessage(f"Bote a pintar nombre: {bote.Name()}")

                partes_bote = bote.Childs()

                for i in range(0,3):
                    if pintura_nombre in partes_bote[i].Name():
                        pintura = partes_bote[i]
                        break
                    else:
                        pintura = RDK_hilo_pintado_interior.Item(pintura_nombre)

                RDK_hilo_pintado_interior.ShowMessage("Voy a coger de la cola de colores")

                rgb = Init.cola_colores_interior.get()

                RDK_hilo_pintado_interior.ShowMessage("He cogido de la cola")

                # DESCOMPOSICION DEL RGB
                r_hex = rgb[0:2]
                g_hex = rgb[2:4]
                b_hex = rgb[4:6]

                r = int(r_hex, 16) / 255
                g = int(g_hex, 16) / 255
                b = int(b_hex, 16) / 255

                pintura.setColor([r,g,b,1])

                RDK_hilo_pintado_interior.ShowMessage("He pintado el bote")
                time.sleep(2)

            time.sleep(0.5)

# -------------------------------------------------------------------------------------------------------------