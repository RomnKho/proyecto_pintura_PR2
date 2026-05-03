
# You can also use the new version of the API:
from robodk.robolink import *    # RoboDK API
from robodk.robomath import *   # Robot toolbox

RDK = Robolink()


def move_cinta(cantidad, rgb):

    incremento = 300
    bote_pintura_interior_v = []    # Creo una lista para cuando duplique el cubo y este cambie de color que el cubo copiado no tengo esos cambios
                                    # Asi tambien se puede evitar usar variables globales

    # DESCOMPOSICION DEL RGB
    r_hex = rgb[0:2]
    g_hex = rgb[2:4] 
    b_hex = rgb[4:6]

    r = int(r_hex, 16) / 255
    g = int(g_hex, 16) / 255
    b = int(b_hex, 16) / 255

    # DEFINICION DE OBJETOS 
    cintaInterior = RDK.Item("[INTERIOR] CintaMovil")

    bote_pintura_interior_obj = RDK.Item("PR2_bote_pintura_rotado", ITEM_TYPE_OBJECT)
    bote_pintura_interior_v.append(bote_pintura_interior_obj) # Añado el primer cubo

    frame_cinta = RDK.Item("[INTERIOR] FrameCinta", ITEM_TYPE_FRAME)
    pintura = RDK.Item("PR2_bote_liquido")

    # MOVER LA CINTA Y MULTIPLICAR LOS BOTES
    if cintaInterior.Valid() and bote_pintura_interior_obj.Valid() and frame_cinta.Valid():

        for i in range(1,int(cantidad)): # Aqui va la cantidad del pedido
            cintaInterior.MoveJ(cintaInterior.Joints() + incremento)

            bote_pintura_interior_v[0].Copy() # Copio el ultimo añadido a la lista
            bote_pintura_interior_copy = RDK.Paste(frame_cinta) 
            bote_pintura_interior_v.append(bote_pintura_interior_copy) # Añado el siguiente cubo
            
            bote_pintura_interior_copy.setPose(bote_pintura_interior_v[0].Pose() * robomath.transl(-incremento, 0, 0))

            x_bote = bote_pintura_interior_v[0].Pose().rows[0][0]

            if (x_bote + 900) >= 900:
                pintura.setColor([r,g,b,1])

            bote_pintura_interior_v.pop(0) # Elimino el bote ya preparado de la lista

# -------------------------------------------------------------------------------------------------------------