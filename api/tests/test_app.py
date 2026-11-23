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

@pytest.fixture
def c(tmp_path, monkeypatch):
    monkeypatch.setattr(miapp, "obtener_conexion", shim.preparar(str(tmp_path / "t.db")))
    return miapp.app.test_client()

def entrar(c, u="1234567890", p="secreto1"):
    c.post("/api/registro", json={"username": u, "password": p})
    t = c.post("/api/login", json={"username": u, "password": p}).get_json()["token"]
    return {"Authorization": "Bearer " + t}

def test_salud(c): assert c.get("/api/salud").status_code == 200

def test_registro_y_duplicado(c):
    assert c.post("/api/registro", json={"username": "1234567890", "password": "secreto1"}).status_code == 201
    assert c.post("/api/registro", json={"username": "1234567890", "password": "secreto1"}).status_code == 409

@pytest.mark.parametrize("u,p", [("abc", "secreto1"), ("1234567890", "123"), ("", ""), (None, None)])
def test_registro_invalido(c, u, p):
    assert c.post("/api/registro", json={"username": u, "password": p}).status_code == 400

def test_login_bien_y_mal(c):
    h = entrar(c)
    assert c.post("/api/login", json={"username": "1234567890", "password": "mala"}).status_code == 401
    assert c.get("/api/me", headers=h).get_json()["username"] == "1234567890"

def test_sin_token_401(c):
    for ruta in ["/api/me", "/api/agendamientos", "/api/traslados", "/api/agendamientos/csv", "/api/usuarios/1234567890"]:
        assert c.get(ruta).status_code == 401
    assert c.get("/api/me", headers={"Authorization": "Bearer falso"}).status_code == 401

def test_usuarios_solo_propio(c):
    h = entrar(c)
    entrar(c, "9999999999")
    assert c.get("/api/usuarios/1234567890", headers=h).status_code == 200
    assert c.get("/api/usuarios/9999999999", headers=h).status_code == 403
    assert c.delete("/api/usuarios/9999999999", headers=h).status_code == 403
    assert c.put("/api/usuarios/9999999999", json={"password": "nueva123"}, headers=h).status_code == 403

def test_cambiar_clave_y_borrar(c):
    h = entrar(c)
    assert c.put("/api/usuarios/1234567890", json={"password": "nueva123"}, headers=h).status_code == 200
    assert c.post("/api/login", json={"username": "1234567890", "password": "nueva123"}).status_code == 200
    assert c.delete("/api/usuarios/1234567890", headers=h).status_code == 200
    assert c.post("/api/login", json={"username": "1234567890", "password": "nueva123"}).status_code == 401

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
