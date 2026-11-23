# Ruta de la Salud

Carpeta `api/` → servidor Flask + MySQL. Carpeta `web/` → páginas HTML/CSS/JS.

## Probar en tu computador
1. En MySQL (Workbench o phpMyAdmin) ejecuta `api/database.sql`.
2. En `api/`, copia `.env.example` a `.env` y escribe tu contraseña de MySQL en `DB_PASSWORD`.
3. Terminal dentro de `api/`:
   ```
   pip install -r requirements.txt
   python app.py
   ```
4. Abre `web/00_crear_usuario.html` (mejor con la extensión Live Server de VS Code), crea un usuario e inicia sesión.
5. Pruebas automáticas (opcional): `pip install pytest` y `python -m pytest tests -q`.

## Qué cambió
- Agendamientos y traslados ahora se guardan en MySQL (antes en el navegador).
- Inicio de sesión con token; sin sesión las páginas internas devuelven al login.
- Cada usuario solo puede ver/cambiar/borrar su propia cuenta (antes cualquiera podía).
- Descarga real de las bases en CSV (se abre en Excel).
- Configuración por variables de entorno (`.env`), sin contraseñas en el código.

## Publicar (paso 2, lo hacemos juntos)
Base de datos: TiDB Cloud · API: Render (`Root Directory = api`, Start Command `gunicorn app:app`) · Página: Cloudflare Pages o Netlify (carpeta `web`). Al final se cambia `API_URL` en `web/js/config.js`.
