-- =========================================================
-- Script de creación de base de datos y tabla para el
-- servicio de registro e inicio de sesión (API de autenticación)
-- =========================================================

-- Crear la base de datos (si no existe)
CREATE DATABASE IF NOT EXISTS auth_db;
USE auth_db;

-- Crear la tabla de usuarios
-- La contraseña NUNCA se guarda en texto plano, se guarda con hash (bcrypt)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,  -- aquí se guarda el hash, no la contraseña real
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
