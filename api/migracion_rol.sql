-- Migración: agrega el rol a la tabla usuarios que ya existe.
-- Ejecutar UNA sola vez en cada base de datos (local y TiDB Cloud).
USE ruta_salud_db;
ALTER TABLE usuarios ADD COLUMN rol VARCHAR(10) NOT NULL DEFAULT 'usuario';
