# Ruta de la Salud

Sistema web para registrar y consultar agendamientos y traslados de pacientes.

- `api/`: servicio REST en Flask (Python) con base de datos MySQL.
- `web/`: interfaz en HTML, CSS y JavaScript.

## Funcionalidades
- Inicio de sesión con token (contraseñas cifradas con bcrypt) y dos roles: administrador y usuario.
- El administrador crea, lista y elimina usuarios desde la página «Administrar usuarios»; el registro público está cerrado.
- Registro y consulta de agendamientos y traslados, guardados en MySQL.
- Descarga de las bases en formato CSV (compatible con Excel).
- Cada usuario solo puede consultar su propia cuenta y cambiar su propia contraseña.
- Configuración mediante variables de entorno.

## Ejecución en entorno local
1. Ejecutar `api/database.sql` en MySQL (Workbench o phpMyAdmin).
2. En `api/`, copiar `.env.example` como `.env` y completar `DB_PASSWORD`, `ADMIN_DOCUMENTO` y `ADMIN_PASSWORD` (el administrador inicial se crea al arrancar la API). Si la tabla `usuarios` ya existía, ejecutar antes `api/migracion_rol.sql`.
3. Dentro de `api/`:
   ```
   pip install -r requirements.txt
   python app.py
   ```
4. Abrir `web/01_Login.html` en el navegador (o con Live Server de VS Code) e iniciar sesión con el administrador; desde «Administrar usuarios» se crean las demás cuentas.
5. Pruebas automáticas de la API: `pip install pytest` y `python -m pytest tests -q`.

## Despliegue (planes gratuitos)
- Base de datos: TiDB Cloud Starter (MySQL compatible, conexión cifrada con `DB_SSL=1`).
- API: Render (`Root Directory = api`, Build `pip install -r requirements.txt`, Start `gunicorn app:app`).
- Página web: Netlify (carpeta `web`). La dirección de la API se configura en `web/js/config.js`.

Variables de entorno de la API: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_SSL`, `SECRET_KEY`, `CORS_ORIGINS`, `ADMIN_DOCUMENTO`, `ADMIN_PASSWORD`.
