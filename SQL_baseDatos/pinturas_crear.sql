CREATE SCHEMA pinturas;
SET search_path TO pinturas;

CREATE TABLE productos ( 
    id_producto SERIAL PRIMARY KEY, 
    nombre VARCHAR(100) NOT NULL, 
    tipo VARCHAR(20) NOT NULL, 
    volumen_litros DECIMAL(5,2) NOT NULL, 
    descripcion TEXT 
);

CREATE TABLE recetas_color ( 
    id_receta SERIAL PRIMARY KEY, 
    nombre_color VARCHAR(100) NOT NULL, 
    codigo_color VARCHAR(50) NOT NULL, 
    tipo_receta VARCHAR(20) NOT NULL CHECK (tipo_receta IN ('Generica', 'Personalizada')), 
    valor_rojo INT NOT NULL, 
    valor_verde INT NOT NULL, 
    valor_azul INT NOT NULL, 
    cantidad_rojo_ml DECIMAL(8,2) NOT NULL, 
    cantidad_verde_ml DECIMAL(8,2) NOT NULL, 
    cantidad_azul_ml DECIMAL(8,2) NOT NULL, 
    tiempo_agitado_seg INT NOT NULL 
);

CREATE TABLE lineas ( 
    id_linea SERIAL PRIMARY KEY, 
    nombre VARCHAR(100) NOT NULL, 
    tipo_pintura VARCHAR(20) NOT NULL, 
    activa VARCHAR(2) NOT NULL 
);

CREATE TABLE maquinas ( 
    id_maquina SERIAL PRIMARY KEY, 
    nombre VARCHAR(100) NOT NULL, 
    tipo VARCHAR(50) NOT NULL, 
    activa VARCHAR(2) NOT NULL
);



CREATE TABLE maquinas_lineas (  
    id_maquina INT NOT NULL,  
    id_linea INT NOT NULL,  
    PRIMARY KEY (id_maquina, id_linea),  
    FOREIGN KEY (id_maquina) REFERENCES maquinas(id_maquina),  
    FOREIGN KEY (id_linea) REFERENCES lineas(id_linea)  
);

CREATE TABLE cubos (   
    id_cubo SERIAL PRIMARY KEY,  
    codigo_cubo VARCHAR(50) NOT NULL,   
    id_producto INT NOT NULL,  
    id_receta INT NOT NULL,   
    id_linea INT NOT NULL,   
    fecha_prod TIMESTAMP NOT NULL,   
    FOREIGN KEY (id_producto) REFERENCES productos(id_producto),   
    FOREIGN KEY (id_receta) REFERENCES recetas_color(id_receta),   
    FOREIGN KEY (id_linea) REFERENCES lineas(id_linea)   
);