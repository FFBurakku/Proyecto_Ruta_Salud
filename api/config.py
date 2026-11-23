# =========================================================
# config.py
# Configuración de la API de Ruta de la Salud.
#
# Los valores se leen de variables de entorno. En tu computador
# se cargan desde un archivo ".env" (ver ".env.example"); en el
# servidor de producción (Render) se escriben en el panel de la
# plataforma. Así NO se guardan contraseñas dentro del código.
# =========================================================

import os
from dotenv import load_dotenv

load_dotenv()  # lee el archivo .env si existe (solo se usa en local)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "ruta_salud_db"),
}

# Bases de datos en la nube (como TiDB Cloud) exigen conexión cifrada (SSL/TLS).
# Con DB_SSL=1 se activa y se verifica el certificado del servidor.
if os.getenv("DB_SSL", "0") == "1":
    DB_CONFIG["ssl_disabled"] = False
    DB_CONFIG["ssl_ca"] = os.getenv("DB_SSL_CA", "/etc/ssl/certs/ca-certificates.crt")
    DB_CONFIG["ssl_verify_cert"] = True
    DB_CONFIG["ssl_verify_identity"] = True

# Clave secreta para firmar los tokens de sesión. En producción es OBLIGATORIA
# y debe ser un texto largo y aleatorio que solo tú conozcas.
SECRET_KEY = os.getenv("SECRET_KEY")

# Horas que dura una sesión antes de pedir iniciar sesión de nuevo
TOKEN_HORAS = int(os.getenv("TOKEN_HORAS", "8"))

# Direcciones desde las que el frontend puede llamar a la API (CORS).
# En local: "*". En producción: la dirección de tu página, por ejemplo
# "https://ruta-salud.pages.dev" (varias se separan con comas).
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
