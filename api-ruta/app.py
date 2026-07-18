from flask import Flask, request, jsonify
from flask_cors import CORS  # permite que el frontend (otro puerto/origen) llame a esta API
import mysql.connector
from mysql.connector import Error
import bcrypt  # librería para encriptar (hashear) contraseñas de forma segura
from config import DB_CONFIG

app = Flask(__name__)
CORS(app)  # habilita CORS para todas las rutas, necesario para que el HTML/JS pueda consumir la API


def obtener_conexion():
    """
    Crea y retorna una conexión a la base de datos MySQL
    usando los datos definidos en config.py.
    """
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        return conexion
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None


@app.route("/api/registro", methods=["POST"])
def registro():
    """
    Endpoint para registrar un nuevo usuario.
    Espera un JSON con 'username' y 'password'.
    Guarda la contraseña encriptada (hash), nunca en texto plano.
    """
    datos = request.get_json()

    # Validar que llegaron los datos requeridos
    if not datos or "username" not in datos or "password" not in datos:
        return jsonify({"mensaje": "Debe enviar username y password"}), 400

    username = datos["username"].strip()
    password = datos["password"]

    if username == "" or password == "":
        return jsonify({"mensaje": "username y password no pueden estar vacíos"}), 400

    # Generar el hash de la contraseña antes de guardarla
    hash_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    conexion = obtener_conexion()
    if conexion is None:
        return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conexion.cursor()
        # Insertar el nuevo usuario en la tabla 'usuarios'
        cursor.execute(
            "INSERT INTO usuarios (username, password) VALUES (%s, %s)",
            (username, hash_password.decode("utf-8"))
        )
        conexion.commit()
        return jsonify({"mensaje": "Usuario registrado correctamente"}), 201

    except mysql.connector.IntegrityError:
        # Se dispara si el username ya existe (columna UNIQUE)
        return jsonify({"mensaje": "El usuario ya existe"}), 409

    except Error as e:
        return jsonify({"mensaje": f"Error al registrar el usuario: {e}"}), 500

    finally:
        cursor.close()
        conexion.close()


@app.route("/api/login", methods=["POST"])
def login():
    """
    Endpoint para iniciar sesión.
    Espera un JSON con 'username' y 'password'.
    Compara la contraseña recibida con el hash guardado en la base de datos.
    """
    datos = request.get_json()

    if not datos or "username" not in datos or "password" not in datos:
        return jsonify({"mensaje": "Debe enviar username y password"}), 400

    username = datos["username"].strip()
    password = datos["password"]

    conexion = obtener_conexion()
    if conexion is None:
        return jsonify({"mensaje": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conexion.cursor(dictionary=True)
        # Buscar al usuario por su username
        cursor.execute(
            "SELECT * FROM usuarios WHERE username = %s",
            (username,)
        )
        usuario = cursor.fetchone()

        # Si no existe el usuario, la autenticación falla
        if usuario is None:
            return jsonify({"mensaje": "Error en la autenticación"}), 401

        # Verificar la contraseña comparando contra el hash guardado
        password_correcta = bcrypt.checkpw(
            password.encode("utf-8"),
            usuario["password"].encode("utf-8")
        )

        if password_correcta:
            return jsonify({"mensaje": "Autenticación satisfactoria"}), 200
        else:
            return jsonify({"mensaje": "Error en la autenticación"}), 401

    except Error as e:
        return jsonify({"mensaje": f"Error al iniciar sesión: {e}"}), 500

    finally:
        cursor.close()
        conexion.close()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
