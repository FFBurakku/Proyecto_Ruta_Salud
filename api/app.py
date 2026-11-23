# =========================================================
# app.py - API de Ruta de la Salud (Flask + MySQL)
# =========================================================

import csv
import io
import os
import re
from datetime import date, datetime, time as dtime, timedelta
from functools import wraps

import bcrypt
from flask import Flask, jsonify, request, Response, g
from flask_cors import CORS
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

import config

app = Flask(__name__)
CORS(app, origins=config.CORS_ORIGINS)

if not config.SECRET_KEY:
    # En producción debe definirse SECRET_KEY. En local se usa una clave de desarrollo.
    if os.getenv("FLASK_ENV") == "production" or os.getenv("RENDER"):
        raise RuntimeError("Falta la variable de entorno SECRET_KEY")
    SECRET = "clave-solo-para-desarrollo"
else:
    SECRET = config.SECRET_KEY

serializador = URLSafeTimedSerializer(SECRET, salt="ruta-salud-sesion")


# ---------- Utilidades ----------

def obtener_conexion():
    import mysql.connector
    return mysql.connector.connect(**config.DB_CONFIG)


def error(mensaje, codigo=400):
    return jsonify({"error": mensaje}), codigo


def crear_token(username):
    return serializador.dumps({"u": username})


def requiere_sesion(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        cabecera = request.headers.get("Authorization", "")
        if not cabecera.startswith("Bearer "):
            return error("Debes iniciar sesión", 401)
        try:
            datos = serializador.loads(cabecera[7:], max_age=config.TOKEN_HORAS * 3600)
        except SignatureExpired:
            return error("La sesión expiró, inicia sesión de nuevo", 401)
        except BadSignature:
            return error("Sesión no válida", 401)
        # El rol se consulta en cada petición: si el usuario fue eliminado
        # o cambió de rol, el token deja de tener efecto de inmediato.
        con = obtener_conexion()
        try:
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT rol FROM usuarios WHERE username=%s", (datos["u"],))
            u = cur.fetchone()
        finally:
            con.close()
        if not u:
            return error("Sesión no válida", 401)
        g.usuario = datos["u"]
        g.rol = u["rol"]
        return f(*args, **kwargs)
    return envoltura


def requiere_admin(f):
    @wraps(f)
    @requiere_sesion
    def envoltura(*args, **kwargs):
        if g.rol != "admin":
            return error("Solo el administrador puede realizar esta acción", 403)
        return f(*args, **kwargs)
    return envoltura


_admin_listo = False


def asegurar_admin():
    """Crea el administrador inicial a partir de ADMIN_DOCUMENTO y ADMIN_PASSWORD."""
    global _admin_listo
    if _admin_listo or not config.ADMIN_DOCUMENTO or not config.ADMIN_PASSWORD:
        return
    con = obtener_conexion()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM usuarios WHERE username=%s", (config.ADMIN_DOCUMENTO,))
        if cur.fetchone():
            cur.execute("UPDATE usuarios SET rol='admin' WHERE username=%s", (config.ADMIN_DOCUMENTO,))
        else:
            h = bcrypt.hashpw(config.ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
            cur.execute("INSERT INTO usuarios (username,password,rol) VALUES (%s,%s,'admin')",
                        (config.ADMIN_DOCUMENTO, h))
        con.commit()
        _admin_listo = True
    finally:
        con.close()


@app.before_request
def preparar_admin():
    try:
        asegurar_admin()
    except Exception as e:  # no bloquear la API si la base aún no responde
        app.logger.warning("No se pudo verificar el administrador: %s", e)


def validar_credenciales(username, password):
    if not isinstance(username, str) or not re.fullmatch(r"\d{5,15}", username.strip()):
        return "El documento debe tener entre 5 y 15 números"
    if not isinstance(password, str) or len(password) < 6 or len(password) > 72:
        return "La contraseña debe tener entre 6 y 72 caracteres"
    return None


def a_texto(valor):
    """Convierte fechas/horas de MySQL a texto para JSON."""
    if isinstance(valor, timedelta):  # MySQL devuelve TIME como timedelta
        s = int(valor.total_seconds())
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}"
    if isinstance(valor, dtime):
        return valor.strftime("%H:%M")
    if isinstance(valor, (date, datetime)):
        return valor.strftime("%Y-%m-%d") if not isinstance(valor, datetime) else valor.strftime("%Y-%m-%d %H:%M")
    return valor


def fila_a_dict(fila):
    return {k: a_texto(v) for k, v in fila.items()}


# ---------- Definición de los registros ----------

TIPOS_DOC = {"CC", "TI", "RC"}

CAMPOS_AGENDAMIENTO = ["tipo_documento", "documento", "nombre", "apellidos", "edad",
                       "fecha", "origen", "destino", "hora", "motivo"]
CAMPOS_TRASLADO = ["tipo_documento", "documento", "nombre", "apellidos", "fecha",
                   "hora_origen", "hora_llegada", "placa", "origen", "destino"]
LARGO_MAX = {"nombre": 80, "apellidos": 80, "origen": 80, "destino": 80,
             "motivo": 200, "placa": 10, "documento": 20}


def limpiar(datos, campos):
    """Devuelve (valores, mensaje_de_error)."""
    if not isinstance(datos, dict):
        return None, "Datos no válidos"
    v = {}
    for c in campos:
        x = datos.get(c)
        if x is None or str(x).strip() == "":
            return None, f"Falta el campo: {c}"
        v[c] = str(x).strip()
        if c in LARGO_MAX and len(v[c]) > LARGO_MAX[c]:
            return None, f"El campo {c} es demasiado largo"
    if v["tipo_documento"] not in TIPOS_DOC:
        return None, "Tipo de documento no válido"
    if not re.fullmatch(r"\d{5,20}", v["documento"]):
        return None, "El documento debe contener solo números"
    for c in ("fecha",):
        try:
            datetime.strptime(v[c], "%Y-%m-%d")
        except ValueError:
            return None, "Fecha no válida"
    for c in ("hora", "hora_origen", "hora_llegada"):
        if c in v and not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", v[c]):
            return None, "Hora no válida"
    if "edad" in v:
        if not v["edad"].isdigit() or not (0 <= int(v["edad"]) <= 120):
            return None, "Edad no válida"
        v["edad"] = int(v["edad"])
    if "placa" in v:
        v["placa"] = v["placa"].upper()
        if not re.fullmatch(r"[A-Z0-9-]{5,10}", v["placa"]):
            return None, "Placa no válida"
    return v, None


def insertar(tabla, campos, valores, usuario):
    cols = ",".join(campos) + ",registrado_por"
    marcas = ",".join(["%s"] * (len(campos) + 1))
    con = obtener_conexion()
    try:
        cur = con.cursor()
        cur.execute(f"INSERT INTO {tabla} ({cols}) VALUES ({marcas})",
                    [valores[c] for c in campos] + [usuario])
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def listar(tabla, campos):
    con = obtener_conexion()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute(f"SELECT id,{','.join(campos)} FROM {tabla} ORDER BY fecha DESC, id DESC")
        return [fila_a_dict(f) for f in cur.fetchall()]
    finally:
        con.close()


def celda_segura(valor):
    """Evita que Excel ejecute fórmulas (CSV injection)."""
    s = "" if valor is None else str(valor)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s


def respuesta_csv(filas, campos, nombre):
    salida = io.StringIO()
    escritor = csv.writer(salida, delimiter=";")
    escritor.writerow(campos)
    for f in filas:
        escritor.writerow([celda_segura(f.get(c)) for c in campos])
    # BOM para que Excel abra bien las tildes y ñ
    cuerpo = "﻿" + salida.getvalue()
    return Response(cuerpo, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename={nombre}"})


# ---------- Rutas ----------

@app.route("/")
@app.route("/api/salud")
def salud():
    return jsonify({"estado": "ok", "servicio": "API Ruta de la Salud"})


@app.route("/api/login", methods=["POST"])
def login():
    d = request.get_json(silent=True) or {}
    username, password = d.get("username"), d.get("password")
    if not isinstance(username, str) or not isinstance(password, str) or not username or not password:
        return error("Documento y contraseña son obligatorios")
    con = obtener_conexion()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT username,password,rol FROM usuarios WHERE username=%s", (username.strip(),))
        u = cur.fetchone()
    finally:
        con.close()
    if not u or not bcrypt.checkpw(password.encode(), u["password"].encode()):
        return error("Documento o contraseña incorrectos", 401)
    return jsonify({"mensaje": "Inicio de sesión exitoso", "token": crear_token(u["username"]),
                    "username": u["username"], "rol": u["rol"]})


@app.route("/api/me")
@requiere_sesion
def me():
    return jsonify({"username": g.usuario, "rol": g.rol})


# ----- Gestión de usuarios -----
# El administrador crea, lista y elimina usuarios. Cada usuario puede ver su
# propia cuenta y cambiar su propia contraseña.

@app.route("/api/usuarios", methods=["GET"])
@requiere_admin
def listar_usuarios():
    con = obtener_conexion()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT id,username,rol,fecha_registro FROM usuarios ORDER BY id")
        return jsonify([fila_a_dict(f) for f in cur.fetchall()])
    finally:
        con.close()


@app.route("/api/usuarios", methods=["POST"])
@requiere_admin
def crear_usuario():
    d = request.get_json(silent=True) or {}
    username, password = d.get("username"), d.get("password")
    rol = d.get("rol", "usuario")
    msg = validar_credenciales(username, password)
    if msg:
        return error(msg)
    if rol not in ("admin", "usuario"):
        return error("Rol no válido")
    username = username.strip()
    hash_ = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    con = obtener_conexion()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM usuarios WHERE username=%s", (username,))
        if cur.fetchone():
            return error("Ese documento ya está registrado", 409)
        cur.execute("INSERT INTO usuarios (username,password,rol) VALUES (%s,%s,%s)",
                    (username, hash_, rol))
        con.commit()
    finally:
        con.close()
    return jsonify({"mensaje": "Usuario creado correctamente"}), 201


def puede_gestionar(username):
    return username == g.usuario or g.rol == "admin"


@app.route("/api/usuarios/<username>", methods=["GET"])
@requiere_sesion
def ver_usuario(username):
    if not puede_gestionar(username):
        return error("No tienes permiso para esta acción", 403)
    con = obtener_conexion()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT id,username,rol,fecha_registro FROM usuarios WHERE username=%s", (username,))
        u = cur.fetchone()
    finally:
        con.close()
    if not u:
        return error("Usuario no encontrado", 404)
    return jsonify(fila_a_dict(u))


@app.route("/api/usuarios/<username>", methods=["PUT"])
@requiere_sesion
def cambiar_clave(username):
    if not puede_gestionar(username):
        return error("No tienes permiso para esta acción", 403)
    d = request.get_json(silent=True) or {}
    msg = validar_credenciales(username, d.get("password"))
    if msg:
        return error(msg)
    hash_ = bcrypt.hashpw(d["password"].encode(), bcrypt.gensalt()).decode()
    con = obtener_conexion()
    try:
        cur = con.cursor()
        cur.execute("UPDATE usuarios SET password=%s WHERE username=%s", (hash_, username))
        con.commit()
    finally:
        con.close()
    return jsonify({"mensaje": "Contraseña actualizada"})


@app.route("/api/usuarios/<username>", methods=["DELETE"])
@requiere_admin
def borrar_usuario(username):
    if username == g.usuario:
        return error("No puedes eliminar tu propia cuenta de administrador", 400)
    con = obtener_conexion()
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM usuarios WHERE username=%s", (username,))
        con.commit()
    finally:
        con.close()
    return jsonify({"mensaje": "Usuario eliminado"})


@app.route("/api/agendamientos", methods=["GET"])
@requiere_sesion
def get_agendamientos():
    return jsonify(listar("agendamientos", CAMPOS_AGENDAMIENTO))


@app.route("/api/agendamientos", methods=["POST"])
@requiere_sesion
def post_agendamiento():
    v, msg = limpiar(request.get_json(silent=True), CAMPOS_AGENDAMIENTO)
    if msg:
        return error(msg)
    nuevo = insertar("agendamientos", CAMPOS_AGENDAMIENTO, v, g.usuario)
    return jsonify({"mensaje": "Agendamiento guardado", "id": nuevo}), 201


@app.route("/api/traslados", methods=["GET"])
@requiere_sesion
def get_traslados():
    return jsonify(listar("traslados", CAMPOS_TRASLADO))


@app.route("/api/traslados", methods=["POST"])
@requiere_sesion
def post_traslado():
    v, msg = limpiar(request.get_json(silent=True), CAMPOS_TRASLADO)
    if msg:
        return error(msg)
    nuevo = insertar("traslados", CAMPOS_TRASLADO, v, g.usuario)
    return jsonify({"mensaje": "Traslado guardado", "id": nuevo}), 201


@app.route("/api/agendamientos/csv")
@requiere_sesion
def csv_agendamientos():
    return respuesta_csv(listar("agendamientos", CAMPOS_AGENDAMIENTO),
                         CAMPOS_AGENDAMIENTO, "agendamientos.csv")


@app.route("/api/traslados/csv")
@requiere_sesion
def csv_traslados():
    return respuesta_csv(listar("traslados", CAMPOS_TRASLADO),
                         CAMPOS_TRASLADO, "traslados.csv")


@app.errorhandler(500)
def error_interno(_):
    return error("Error interno del servidor", 500)


if __name__ == "__main__":
    # Solo para desarrollo local. En producción se usa gunicorn.
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1", port=5000)
