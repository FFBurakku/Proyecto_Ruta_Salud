import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import shim
import app as miapp

AG = dict(tipo_documento="CC", documento="1020304050", nombre="Ana", apellidos="Pérez",
          edad=34, fecha="2026-12-01", origen="01. USS Simon Bolivar", destino="14. CSE Suba",
          hora="08:30", motivo="Control")
TR = dict(tipo_documento="CC", documento="1020304050", nombre="Ana", apellidos="Pérez",
          fecha="2026-12-01", hora_origen="07:00", hora_llegada="08:00", placa="abc123",
          origen="01. USS Simon Bolivar", destino="14. CSE Suba")

ADMIN = ("1000000001", "adminclave1")

@pytest.fixture
def c(tmp_path, monkeypatch):
    monkeypatch.setattr(miapp, "obtener_conexion", shim.preparar(str(tmp_path / "t.db")))
    monkeypatch.setattr(miapp.config, "ADMIN_DOCUMENTO", ADMIN[0])
    monkeypatch.setattr(miapp.config, "ADMIN_PASSWORD", ADMIN[1])
    monkeypatch.setattr(miapp, "_admin_listo", False)
    return miapp.app.test_client()

def sesion(c, u, p):
    r = c.post("/api/login", json={"username": u, "password": p})
    return {"Authorization": "Bearer " + r.get_json()["token"]}

def admin(c):
    return sesion(c, *ADMIN)

def entrar(c, u="1234567890", p="secreto1"):
    """Crea un usuario normal (lo hace el administrador) y devuelve sus cabeceras."""
    c.post("/api/usuarios", json={"username": u, "password": p}, headers=admin(c))
    return sesion(c, u, p)

def test_salud(c): assert c.get("/api/salud").status_code == 200

def test_admin_inicial_creado_y_con_rol(c):
    r = c.post("/api/login", json={"username": ADMIN[0], "password": ADMIN[1]})
    assert r.status_code == 200 and r.get_json()["rol"] == "admin"

def test_registro_publico_ya_no_existe(c):
    assert c.post("/api/registro", json={"username": "1234567890", "password": "secreto1"}).status_code in (404, 405)

def test_crear_usuario_requiere_admin(c):
    assert c.post("/api/usuarios", json={"username": "1234567890", "password": "secreto1"}).status_code == 401
    h = entrar(c)
    assert c.post("/api/usuarios", json={"username": "5555555555", "password": "secreto1"}, headers=h).status_code == 403

def test_admin_crea_y_duplicado(c):
    h = admin(c)
    assert c.post("/api/usuarios", json={"username": "1234567890", "password": "secreto1"}, headers=h).status_code == 201
    assert c.post("/api/usuarios", json={"username": "1234567890", "password": "secreto1"}, headers=h).status_code == 409

@pytest.mark.parametrize("d", [dict(username="abc", password="secreto1"), dict(username="1234567890", password="123"),
                               dict(username="", password=""), dict(username="1234567890", password="secreto1", rol="dios")])
def test_creacion_invalida(c, d):
    assert c.post("/api/usuarios", json=d, headers=admin(c)).status_code == 400

def test_login_bien_y_mal(c):
    h = entrar(c)
    assert c.post("/api/login", json={"username": "1234567890", "password": "mala"}).status_code == 401
    r = c.get("/api/me", headers=h).get_json()
    assert r == {"username": "1234567890", "rol": "usuario"}

def test_sin_token_401(c):
    for ruta in ["/api/me", "/api/agendamientos", "/api/traslados", "/api/agendamientos/csv", "/api/usuarios", "/api/usuarios/1234567890"]:
        assert c.get(ruta).status_code == 401
    assert c.get("/api/me", headers={"Authorization": "Bearer falso"}).status_code == 401

def test_listado_solo_admin_y_sin_hash(c):
    h = entrar(c)
    assert c.get("/api/usuarios", headers=h).status_code == 403
    lista = c.get("/api/usuarios", headers=admin(c)).get_json()
    assert {u["username"] for u in lista} == {ADMIN[0], "1234567890"}
    assert all("password" not in u for u in lista)

def test_usuario_solo_ve_lo_suyo(c):
    h = entrar(c)
    entrar(c, "9999999999")
    assert c.get("/api/usuarios/1234567890", headers=h).status_code == 200
    assert c.get("/api/usuarios/9999999999", headers=h).status_code == 403
    assert c.put("/api/usuarios/9999999999", json={"password": "nueva123"}, headers=h).status_code == 403
    assert c.delete("/api/usuarios/9999999999", headers=h).status_code == 403
    assert c.delete("/api/usuarios/1234567890", headers=h).status_code == 403

def test_cambiar_clave_propia_y_por_admin(c):
    h = entrar(c)
    assert c.put("/api/usuarios/1234567890", json={"password": "nueva123"}, headers=h).status_code == 200
    assert c.post("/api/login", json={"username": "1234567890", "password": "nueva123"}).status_code == 200
    assert c.put("/api/usuarios/1234567890", json={"password": "otraclave9"}, headers=admin(c)).status_code == 200
    assert c.post("/api/login", json={"username": "1234567890", "password": "otraclave9"}).status_code == 200

def test_admin_elimina_y_token_deja_de_servir(c):
    h = entrar(c)
    assert c.get("/api/agendamientos", headers=h).status_code == 200
    assert c.delete("/api/usuarios/1234567890", headers=admin(c)).status_code == 200
    assert c.get("/api/agendamientos", headers=h).status_code == 401
    assert c.post("/api/login", json={"username": "1234567890", "password": "secreto1"}).status_code == 401

def test_admin_no_se_elimina_a_si_mismo(c):
    assert c.delete(f"/api/usuarios/{ADMIN[0]}", headers=admin(c)).status_code == 400

def test_agendamiento_crud(c):
    h = entrar(c)
    r = c.post("/api/agendamientos", json=AG, headers=h)
    assert r.status_code == 201
    lista = c.get("/api/agendamientos", headers=h).get_json()
    assert len(lista) == 1 and lista[0]["nombre"] == "Ana"

def test_traslado_placa_mayuscula(c):
    h = entrar(c)
    assert c.post("/api/traslados", json=TR, headers=h).status_code == 201
    assert c.get("/api/traslados", headers=h).get_json()[0]["placa"] == "ABC123"

@pytest.mark.parametrize("cambio", [dict(tipo_documento="XX"), dict(documento="abc"), dict(fecha="31/12/2026"),
                                    dict(hora="25:00"), dict(edad="200"), dict(nombre=""), dict(motivo="x"*300)])
def test_agendamiento_invalido(c, cambio):
    h = entrar(c)
    assert c.post("/api/agendamientos", json={**AG, **cambio}, headers=h).status_code == 400

def test_csv_con_proteccion(c):
    h = entrar(c)
    c.post("/api/agendamientos", json={**AG, "nombre": "=CMD()"}, headers=h)
    r = c.get("/api/agendamientos/csv", headers=h)
    assert r.status_code == 200 and "attachment" in r.headers["Content-Disposition"]
    txt = r.data.decode("utf-8")
    assert txt.startswith("﻿") and "'=CMD()" in txt and "Pérez" in txt and ";" in txt
