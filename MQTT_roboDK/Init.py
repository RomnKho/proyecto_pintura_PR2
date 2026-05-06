# Script de inicializacion de las colas

from queue import Queue

# Colas para la informacion del pedido
cola_info_pedido_interior = Queue()
cola_info_pedido_exterior = Queue()

# Colas para los botes que se generan
cola_bote_pintura_interior = Queue()
cola_bote_pintura_exterior = Queue()

# Colas con el bote a pintar
cola_bote_a_pintar_interior = Queue()
cola_bote_a_pintar_exterior = Queue()

# Cola con los colores a pintar
cola_colores_interior = Queue()
cola_colores_exterior = Queue()