
# You can also use the new version of the API:
from robodk.robolink import *    # RoboDK API
from robodk.robomath import *   # Robot toolbox

RDK = Robolink()

def move_cinta(rgb, cantidad, tipo):

    incremento = 300
    bote_pintura_v = []     # Creo una lista para cuando duplique el cubo y este cambie de color que el cubo copiado no tengo esos cambios
                            # Asi tambien se puede evitar usar variables globales
    bote_a_pintar_v = []    # Vector con "retraso" para poner la pintura al bote del color correcto despues de los dispensadores

    # DESCOMPOSICION DEL RGB
    r_hex = rgb[0:2]
    g_hex = rgb[2:4] 
    b_hex = rgb[4:6]

    r = int(r_hex, 16) / 255
    g = int(g_hex, 16) / 255
    b = int(b_hex, 16) / 255

    # DEFINICION DE OBJETOS
    if tipo == "Int":
        cinta = RDK.Item("[INTERIOR] CintaMovil")
        frame_cinta = RDK.Item("[INTERIOR] FrameCinta", ITEM_TYPE_FRAME)
        bote_pintura_obj = RDK.Item("[INTERIOR] Bote_pintura", ITEM_TYPE_OBJECT)
        pintura_nombre = "[INTERIOR] Pintura"
    else:
        cinta = RDK.Item("[EXTERIOR] CintaMovil")
        frame_cinta = RDK.Item("[EXTERIOR] FrameCinta", ITEM_TYPE_FRAME)
        bote_pintura_obj = RDK.Item("[EXTERIOR] Bote_pintura", ITEM_TYPE_OBJECT)
        pintura_nombre = "[EXTERIOR] Pintura"

    
    bote_pintura_v.append(bote_pintura_obj) # Añado el primer cubo
    bote_a_pintar_v.append(bote_pintura_obj) # Añado el primer cubo

    # MOVER LA CINTA Y MULTIPLICAR LOS BOTES
    if cinta.Valid() and bote_pintura_obj.Valid() and frame_cinta.Valid():

        for i in range(1,int(cantidad)): # Aqui va la cantidad del pedido
            cinta.MoveJ(cinta.Joints() + incremento)

            bote_pintura_v[0].Copy() # Copio el ultimo bote añadido a la lista
            bote_pintura_copy = RDK.Paste(frame_cinta) 
            bote_pintura_v.append(bote_pintura_copy) # Añado el siguiente bote
            bote_a_pintar_v.append(bote_pintura_copy)
           
            bote_pintura_copy.setPose(bote_pintura_v[0].Pose() * robomath.transl(-incremento, 0, 0))

            x_bote = cinta.Joints().rows[0][0]

            if x_bote >= 900:
                partes_bote = bote_a_pintar_v[0].Childs()

                for i in range(1,3):
                    if pintura_nombre in partes_bote[i].Name():
                        pintura = partes_bote[i]
                        break
                    else:
                        pintura = RDK.Item(pintura_nombre)

                pintura.setColor([r,g,b,1])
                bote_a_pintar_v.pop(0)

            bote_pintura_v.pop(0) # Elimino el bote ya preparado de la lista

# -------------------------------------------------------------------------------------------------------------