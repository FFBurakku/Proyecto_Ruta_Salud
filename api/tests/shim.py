"""Ayudas para probar la API sin MySQL: usa SQLite en memoria/archivo y,
si faltan, reemplaza bcrypt y flask_cors por versiones mínimas."""
import sys, types, sqlite3, hashlib

try:
    import bcrypt  # noqa
except ImportError:
    b = types.ModuleType("bcrypt")
    b.gensalt = lambda: b"salt"
    b.hashpw = lambda p, s: b"$h$" + hashlib.sha256(p).hexdigest().encode()
    b.checkpw = lambda p, h: b.hashpw(p, b"") == h
    sys.modules["bcrypt"] = b
try:
    import flask_cors  # noqa
except ImportError:
    f = types.ModuleType("flask_cors")
    def CORS(app, origins="*"):
        @app.after_request
        def _c(r):
            r.headers["Access-Control-Allow-Origin"] = "*"
            r.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            r.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
            return r
        @app.route("/<path:p>", methods=["OPTIONS"])
        def _o(p):
            return ("", 204)
    f.CORS = CORS
    sys.modules["flask_cors"] = f

SCHEMA = """
CREATE TABLE usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, rol TEXT NOT NULL DEFAULT 'usuario', fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE agendamientos (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo_documento TEXT, documento TEXT, nombre TEXT, apellidos TEXT, edad INT, fecha TEXT, origen TEXT, destino TEXT, hora TEXT, motivo TEXT, registrado_por TEXT, fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE traslados (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo_documento TEXT, documento TEXT, nombre TEXT, apellidos TEXT, fecha TEXT, hora_origen TEXT, hora_llegada TEXT, placa TEXT, origen TEXT, destino TEXT, registrado_por TEXT, fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP);
"""

class _Cur:
    def __init__(self, c, dic): self.c = c; self.dic = dic
    def execute(self, q, p=()):
        self.c.execute(q.replace("%s", "?"), list(p)); return self
    def _d(self, r):
        return dict(r) if (r is not None and self.dic) else r
    def fetchone(self): return self._d(self.c.fetchone())
    def fetchall(self): return [self._d(r) for r in self.c.fetchall()]
    @property
    def lastrowid(self): return self.c.lastrowid

class _Con:
    def __init__(self, path):
        self.k = sqlite3.connect(path); self.k.row_factory = sqlite3.Row
    def cursor(self, dictionary=False): return _Cur(self.k.cursor(), dictionary)
    def commit(self): self.k.commit()
    def close(self): self.k.close()

def preparar(path):
    k = sqlite3.connect(path); k.executescript(SCHEMA); k.commit(); k.close()
    return lambda: _Con(path)
