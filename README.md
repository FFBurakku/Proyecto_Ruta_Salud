# Ruta de la Salud

Sistema web para registrar y consultar agendamientos y traslados de pacientes.

- `api/`: servicio REST en Flask (Python) con base de datos MySQL.
- `web/`: interfaz en HTML, CSS y JavaScript.

## Funcionalidades
- Registro de usuarios e inicio de sesión con token (contraseñas cifradas con bcrypt).
- Registro y consulta de agendamientos y traslados, guardados en MySQL.
- Descarga de las bases en formato CSV (compatible con Excel).
- Cada usuario solo puede consultar, modificar o eliminar su propia cuenta.
- Configuración mediante variables de entorno.

## Ejecución en entorno local
1. Ejecutar `api/database.sql` en MySQL (Workbench o phpMyAdmin).
2. En `api/`, copiar `.env.example` como `.env` y completar la contraseña de MySQL en `DB_PASSWORD`.
3. Dentro de `api/`:
   ```
   pip install -r requirements.txt
   python app.py
   ```
4. Abrir `web/00_crear_usuario.html` en el navegador (o con la extensión Live Server de VS Code), crear un usuario e iniciar sesión.
5. Pruebas automáticas de la API: `pip install pytest` y `python -m pytest tests -q`.

## Despliegue (planes gratuitos)
- Base de datos: TiDB Cloud Starter (MySQL compatible, conexión cifrada con `DB_SSL=1`).
- API: Render (`Root Directory = api`, Build `pip install -r requirements.txt`, Start `gunicorn app:app`).
- Página web: Netlify (carpeta `web`). La dirección de la API se configura en `web/js/config.js`.

Variables de entorno de la API: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_SSL`, `SECRET_KEY`, `CORS_ORIGINS`.
