// =========================================================
// Se ejecuta apenas carga la página: si existe el formulario
// de registro o de login en el HTML actual, le "engancha" el evento submit.
// =========================================================
document.addEventListener("DOMContentLoaded", () => {
    const formRegistro = document.getElementById("formRegistro");
    if (formRegistro) {
        formRegistro.addEventListener("submit", registrarUsuario);
    }

    // Páginas internas: sin sesión se vuelve al login; con sesión se muestra el usuario
    if (document.body.dataset.privada !== undefined) {
        if (!sessionStorage.getItem("token")) {
            window.location.href = "01_Login.html";
            return;
        }
        document.querySelectorAll(".nombre-usuario").forEach(e => {
            e.textContent = sessionStorage.getItem("usuario");
        });
        const salir = document.querySelectorAll(".cerrar-sesion");
        salir.forEach(a => a.addEventListener("click", (ev) => {
            ev.preventDefault();
            cerrarSesion();
        }));
        const tablaA = document.getElementById("tablaAgendamientos");
        const tablaT = document.getElementById("tablaTraslados");
        if (tablaA) mostrarAgendamientos();
        if (tablaT) mostrarTraslados();
    }

    const formLogin = document.getElementById("formLogin");
    if (formLogin) {
        formLogin.addEventListener("submit", iniciarSesion);
    }
});

// =========================================================
// Registro de usuario: envía username y password a la API
// =========================================================
async function registrarUsuario(evento) {
    evento.preventDefault(); // evita que el formulario recargue la página

    let documento = document.getElementById("documento").value;
    let password = document.getElementById("password").value;
    let confirmarPassword = document.getElementById("confirmarPassword").value;
    let mensaje = document.getElementById("mensajeRegistro");

    if (password !== confirmarPassword) {
        mensaje.style.color = "red";
        mensaje.innerText = "Las contraseñas no coinciden";
        return;
    }

    try {
        const respuesta = await fetch(`${API_URL}/api/registro`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            // El documento se envía como "username": es lo que identifica al usuario para el login
            body: JSON.stringify({ username: documento, password })
        });

        const datos = await respuesta.json();

        if (respuesta.ok) {
            mensaje.style.color = "green";
            mensaje.innerText = datos.mensaje;
            // Después de registrar, lo mandamos a la pantalla de login
            setTimeout(() => {
                window.location.href = "01_Login.html";
            }, 1200);
        } else {
            mensaje.style.color = "red";
            mensaje.innerText = datos.error || datos.mensaje;
        }

    } catch (error) {
        // Esto se dispara, por ejemplo, si la API no está corriendo
        mensaje.style.color = "red";
        mensaje.innerText = "No se pudo conectar con el servidor. ¿Está corriendo la API?";
        console.error(error);
    }
}

// =========================================================
// Inicio de sesión: envía username y password a la API
// =========================================================
async function iniciarSesion(evento) {
    evento.preventDefault(); // evita que el formulario recargue la página

    let documento = document.getElementById("documento").value;
    let password = document.getElementById("password").value;
    let mensaje = document.getElementById("mensajeLogin");

    try {
        const respuesta = await fetch(`${API_URL}/api/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: documento, password })
        });

        const datos = await respuesta.json();

        if (respuesta.ok) {
            mensaje.style.color = "green";
            mensaje.innerText = datos.mensaje;
            // Guardamos el token de sesión (se borra al cerrar la pestaña)
            sessionStorage.setItem("token", datos.token);
            sessionStorage.setItem("usuario", datos.username);
            setTimeout(() => {
                window.location.href = "02_menu.html";
            }, 800);
        } else {
            mensaje.style.color = "red";
            mensaje.innerText = datos.error || datos.mensaje;
        }

    } catch (error) {
        mensaje.style.color = "red";
        mensaje.innerText = "No se pudo conectar con el servidor. ¿Está corriendo la API?";
        console.error(error);
    }
}

// =========================================================
// Sesión y llamadas a la API con token
// =========================================================
function cerrarSesion() {
    sessionStorage.clear();
    window.location.href = "01_Login.html";
}

async function llamarApi(ruta, opciones = {}) {
    const respuesta = await fetch(API_URL + ruta, {
        ...opciones,
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + sessionStorage.getItem("token"),
            ...(opciones.headers || {})
        }
    });
    if (respuesta.status === 401) {   // sesión vencida o no válida
        cerrarSesion();
        throw new Error("Sesión expirada");
    }
    return respuesta;
}

// Escapa texto antes de ponerlo en la página (evita inyectar HTML)
function esc(t) {
    const d = document.createElement("div");
    d.textContent = t == null ? "" : String(t);
    return d.innerHTML;
}

// =========================================================
// Formularios de registro
// =========================================================
function limpiarCampos(ids) {
    ids.forEach(id => document.getElementById(id).value = "");
}

async function enviarRegistro(ruta, campos, ids, mensaje, textoOk) {
    mensaje.style.color = "#333";
    mensaje.innerText = "Guardando...";
    try {
        const r = await llamarApi(ruta, { method: "POST", body: JSON.stringify(campos) });
        const d = await r.json();
        if (r.ok) {
            mensaje.style.color = "green";
            mensaje.innerText = textoOk;
            limpiarCampos(ids);
        } else {
            mensaje.style.color = "red";
            mensaje.innerText = d.error || "No se pudo guardar";
        }
    } catch (e) {
        mensaje.style.color = "red";
        mensaje.innerText = "No se pudo conectar con el servidor";
    }
}

function guardarAgendamiento() {
    const ids = ["tipoDocumento", "documento", "nombre", "apellidos", "edad", "fecha", "origen", "destino", "hora", "motivo"];
    const v = Object.fromEntries(ids.map(i => [i, document.getElementById(i).value.trim()]));
    const mensaje = document.getElementById("mensaje");
    if (ids.some(i => v[i] === "")) {
        mensaje.style.color = "red";
        mensaje.innerText = "Por favor complete todos los campos";
        return;
    }
    enviarRegistro("/api/agendamientos", {
        tipo_documento: v.tipoDocumento, documento: v.documento, nombre: v.nombre,
        apellidos: v.apellidos, edad: v.edad, fecha: v.fecha, origen: v.origen,
        destino: v.destino, hora: v.hora, motivo: v.motivo
    }, ids, mensaje, "Agendamiento guardado correctamente");
}

function guardarTraslado() {
    const ids = ["tipoDocumentoT", "documentoT", "nombreT", "apellidosT", "fechaT", "horaOrigen", "horaLlegada", "placa", "origenT", "destinoT"];
    const v = Object.fromEntries(ids.map(i => [i, document.getElementById(i).value.trim()]));
    const mensaje = document.getElementById("mensajeT");
    if (ids.some(i => v[i] === "")) {
        mensaje.style.color = "red";
        mensaje.innerText = "Por favor complete todos los campos";
        return;
    }
    enviarRegistro("/api/traslados", {
        tipo_documento: v.tipoDocumentoT, documento: v.documentoT, nombre: v.nombreT,
        apellidos: v.apellidosT, fecha: v.fechaT, hora_origen: v.horaOrigen,
        hora_llegada: v.horaLlegada, placa: v.placa, origen: v.origenT, destino: v.destinoT
    }, ids, mensaje, "Traslado guardado correctamente");
}

// =========================================================
// Consultas
// =========================================================
async function llenarTabla(ruta, idTabla, columnas) {
    const tabla = document.getElementById(idTabla);
    try {
        const r = await llamarApi(ruta);
        const lista = await r.json();
        if (!r.ok) throw new Error(lista.error);
        if (lista.length === 0) {
            tabla.innerHTML = `<tr><td colspan="${columnas.length + 1}">Aún no hay registros</td></tr>`;
            return;
        }
        tabla.innerHTML = lista.map((it, i) =>
            `<tr><td>${i + 1}</td>${columnas.map(c => `<td>${esc(it[c])}</td>`).join("")}</tr>`
        ).join("");
    } catch (e) {
        tabla.innerHTML = `<tr><td colspan="${columnas.length + 1}">No se pudieron cargar los datos</td></tr>`;
    }
}

function mostrarAgendamientos() {
    llenarTabla("/api/agendamientos", "tablaAgendamientos",
        ["tipo_documento", "documento", "nombre", "apellidos", "origen", "destino", "fecha", "hora"]);
}

function mostrarTraslados() {
    llenarTabla("/api/traslados", "tablaTraslados",
        ["tipo_documento", "documento", "nombre", "apellidos", "origen", "destino", "fecha", "hora_origen", "hora_llegada", "placa"]);
}

// =========================================================
// Descarga de bases en CSV (abre en Excel)
// =========================================================
async function descargarCsv(ruta, nombre) {
    const aviso = document.getElementById("mensajeDescarga");
    try {
        const r = await llamarApi(ruta);
        if (!r.ok) throw new Error();
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = nombre;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        if (aviso) { aviso.style.color = "green"; aviso.innerText = "Descarga lista: " + nombre; }
    } catch (e) {
        if (aviso) { aviso.style.color = "red"; aviso.innerText = "No se pudo descargar el archivo"; }
    }
}
