-- =========================================================
-- Base de datos de Ruta de la Salud
-- Se puede ejecutar varias veces: solo crea lo que falte
-- (si ya tienes la tabla usuarios con datos, no la toca).
-- =========================================================

CREATE DATABASE IF NOT EXISTS ruta_salud_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ruta_salud_db;

-- Usuarios del sistema. La contraseña se guarda con hash (bcrypt), nunca en texto plano.
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,      -- número de documento
    password VARCHAR(255) NOT NULL,            -- hash bcrypt
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agendamientos de citas
CREATE TABLE IF NOT EXISTS agendamientos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo_documento VARCHAR(2) NOT NULL,        -- CC, TI o RC
    documento VARCHAR(20) NOT NULL,
    nombre VARCHAR(80) NOT NULL,
    apellidos VARCHAR(80) NOT NULL,
    edad TINYINT UNSIGNED NOT NULL,
    fecha DATE NOT NULL,                       -- fecha solicitada
    origen VARCHAR(80) NOT NULL,
    destino VARCHAR(80) NOT NULL,
    hora TIME NOT NULL,                        -- hora de llegada
    motivo VARCHAR(200) NOT NULL,
    registrado_por VARCHAR(50) NOT NULL,       -- usuario que hizo el registro
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_agendamientos_fecha (fecha),
    INDEX idx_agendamientos_documento (documento)
);

-- Traslados
CREATE TABLE IF NOT EXISTS traslados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo_documento VARCHAR(2) NOT NULL,
    documento VARCHAR(20) NOT NULL,
    nombre VARCHAR(80) NOT NULL,
    apellidos VARCHAR(80) NOT NULL,
    fecha DATE NOT NULL,
    hora_origen TIME NOT NULL,
    hora_llegada TIME NOT NULL,
    placa VARCHAR(10) NOT NULL,
    origen VARCHAR(80) NOT NULL,
    destino VARCHAR(80) NOT NULL,
    registrado_por VARCHAR(50) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_traslados_fecha (fecha),
    INDEX idx_traslados_documento (documento)
);
