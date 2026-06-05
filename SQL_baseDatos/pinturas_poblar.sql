SET search_path TO pinturas;

INSERT INTO lineas (id_linea,nombre, tipo_pintura, activa
) VALUES 
(1, 'Linea 1','Interior', 'SI'), 
(2, 'Linea 2','Exterior', 'SI'); 
 
INSERT INTO productos (id_producto, nombre, tipo, volumen_litros, descripcion) VALUES 
(1, 'Pintura Interior Blanca', 'Interior', 15.00, 'Pintura blanca para interiores'), 
(2, 'Pintura Interior Mate', 'Interior', 10.00, 'Pintura mate para interiores'), 
(3, 'Pintura Exterior Blanca', 'Exterior', 15.00, 'Pintura blanca para exteriores'), 
(4, 'Pintura Exterior Fachada', 'Exterior', 20.00, 'Pintura para fachadas'); 

INSERT INTO recetas_color ( 
    id_receta, 
    nombre_color, 
    codigo_color, 
    tipo_receta, 
    valor_rojo, 
    valor_verde, 
    valor_azul, 
    cantidad_rojo_ml, 
    cantidad_verde_ml, 
    cantidad_azul_ml, 
    tiempo_agitado_seg 
) VALUES 
(1, 'Blanco Puro', 'GEN001', 'Generica', 255, 255, 255, 0.00, 0.00, 0.00, 60), 
(2, 'Marfil', 'GEN002', 'Generica', 245, 230, 190, 120.00, 90.00, 40.00, 90), 
(3, 'Gris Fachada', 'GEN003', 'Generica', 120, 120, 130, 80.00, 80.00, 100.00, 120), 
(4, 'Color Cliente 1', 'PER001', 'Personalizada', 180, 75, 220, 180.00, 75.00, 220.00, 120), 
(5, 'Color Cliente 2', 'PER002', 'Personalizada', 90, 160, 210, 90.00, 160.00, 210.00, 120); 


INSERT INTO cubos (   
    id_cubo,   
    codigo_cubo,  
    id_producto,   
    id_receta,   
    id_linea, 
    fecha_prod  
) VALUES 
(1, 'CUBO001', 1, 1, 1, TIMESTAMP '2026-04-27 08:00:00'),  
(2, 'CUBO002', 1, 2, 1, TIMESTAMP '2026-04-27 08:02:30'),   
(3, 'CUBO003', 2, 4, 2, TIMESTAMP '2026-04-27 08:05:00'),   
(4, 'CUBO004', 3, 1, 2, TIMESTAMP '2026-04-27 08:07:30'),   
(5, 'CUBO005', 4, 3, 1, TIMESTAMP '2026-04-28 08:05:00'),   
(6, 'CUBO006', 3, 5, 1, TIMESTAMP '2026-04-28 08:08:00'); 
 
INSERT INTO maquinas ( 
    id_maquina, 
    nombre, 
    tipo, 
    activa 
) VALUES 
(11, 'Dispensador Rojo', 'Dispensador_R', 'SI'), 
(12, 'Dispensador Verde', 'Dispensador_G', 'SI'), 
(13, 'Dispensador Azul', 'Dispensador_B', 'SI'), 
(14, 'Etiquetadora', 'Etiquetadora', 'SI'), 
(15, 'Yaskawa HC20SDTP', 'Cobot', 'SI'), 
(16, 'Agitadora 1', 'Agitadora', 'NO'), 
(17, 'Agitadora 2', 'Agitadora', 'SI'), 
(18, 'YASKAWA SG650', 'Scara', 'SI'), 
(19, 'Dispensador Rojo', 'Dispensador_R', 'SI'), 
(20, 'Dispensador Verde', 'Dispensador_G', 'SI'), 
(21, 'Dispensador Azul', 'Dispensador_B', 'SI'), 
(22, 'Etiquetadora', 'Etiquetadora', 'SI'), 
(23, 'Yaskawa HC20SDTP', 'Cobot', 'SI'), 
(24, 'Agitadora 1', 'Agitadora', 'NO'), 
(25, 'Agitadora 2', 'Agitadora', 'SI'), 
(26, 'Yaskawa Motoman GP10', 'Robot', 'SI'); 


INSERT INTO maquinas_lineas ( 
    id_maquina, 
    id_linea 
) VALUES 
(11, 1), 
(12, 1), 
(13, 1), 
(14, 1), 
(15, 1), 
(16, 1), 
(17, 1), 
(18, 1), 
(18, 2), 
(19, 2), 
(20, 2), 
(21, 2), 
(22, 2), 
(23, 2), 
(24, 2), 
(25, 2), 
(26, 1), 
(26, 2);