// =========================================================
// URL base de la API. Si cambias el puerto en app.py, cámbialo aquí también.
// =========================================================
const API_URL = "http://127.0.0.1:5000";

// =========================================================
// Se ejecuta apenas carga la página: si existe el formulario
// de registro o de login en el HTML actual, le "engancha" el evento submit.
// =========================================================
document.addEventListener("DOMContentLoaded", () => {
    const formRegistro = document.getElementById("formRegistro");
    if (formRegistro) {
        formRegistro.addEventListener("submit", registrarUsuario);
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
            mensaje.innerText = datos.mensaje;
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
            mensaje.innerText = datos.mensaje; // "Autenticación satisfactoria"
            setTimeout(() => {
                window.location.href = "02_menu.html";
            }, 800);
        } else {
            mensaje.style.color = "red";
            mensaje.innerText = datos.mensaje; // "Error en la autenticación"
        }

    } catch (error) {
        mensaje.style.color = "red";
        mensaje.innerText = "No se pudo conectar con el servidor. ¿Está corriendo la API?";
        console.error(error);
    }
}

function guardarAgendamiento() {

    let tipoDocumento = document.getElementById("tipoDocumento").value;
    let documento = document.getElementById("documento").value;
    let nombre = document.getElementById("nombre").value;
    let apellidos = document.getElementById("apellidos").value;
    let edad = document.getElementById("edad").value;
    let fecha = document.getElementById("fecha").value;
    let origen = document.getElementById("origen").value;
    let destino = document.getElementById("destino").value;
    let hora = document.getElementById("hora").value;
    let motivo = document.getElementById("motivo").value;

    let mensaje = document.getElementById("mensaje");

    if (
        tipoDocumento === "" ||
        documento === "" ||
        nombre === "" ||
        apellidos === "" ||
        edad === "" ||
        fecha === "" ||
        origen === "" ||
        destino === "" ||
        hora === "" ||
        motivo === ""
    ) {
        mensaje.style.color = "red";
        mensaje.innerText = "Por favor complete todos los campos";
        return;
    }

    let nuevoAgendamiento = {
        tipoDocumento,
        documento,
        nombre,
        apellidos,
        edad,
        fecha,
        origen,
        destino,
        hora,
        motivo
    };

    let lista = JSON.parse(localStorage.getItem("agendamientos")) || [];
    lista.push(nuevoAgendamiento);
    localStorage.setItem("agendamientos", JSON.stringify(lista));

    mensaje.style.color = "green";
    mensaje.innerText = "Agendamiento guardado correctamente";

    document.getElementById("tipoDocumento").value = "";
    document.getElementById("documento").value = "";
    document.getElementById("nombre").value = "";
    document.getElementById("apellidos").value = "";
    document.getElementById("edad").value = "";
    document.getElementById("fecha").value = "";
    document.getElementById("origen").value = "";
    document.getElementById("destino").value = "";
    document.getElementById("hora").value = "";
    document.getElementById("motivo").value = "";
}

function guardarTraslado() {

    let tipoDocumento = document.getElementById("tipoDocumentoT").value;
    let documento = document.getElementById("documentoT").value;
    let nombre = document.getElementById("nombreT").value;
    let apellidos = document.getElementById("apellidosT").value;
    let fecha = document.getElementById("fechaT").value;
    let horaOrigen = document.getElementById("horaOrigen").value;
    let horaLlegada = document.getElementById("horaLlegada").value;
    let placa = document.getElementById("placa").value;
    let origen = document.getElementById("origenT").value;
    let destino = document.getElementById("destinoT").value;

    let mensaje = document.getElementById("mensajeT");

    if (
        tipoDocumento === "" ||
        documento === "" ||
        nombre === "" ||
        apellidos === "" ||
        fecha === "" ||
        horaOrigen === "" ||
        horaLlegada === "" ||
        placa === "" ||
        origen === "" ||
        destino === ""
    ) {
        mensaje.style.color = "red";
        mensaje.innerText = "Por favor complete todos los campos";
        return;
    }

    let nuevoTraslado = {
        tipoDocumento,
        documento,
        nombre,
        apellidos,
        fecha,
        horaOrigen,
        horaLlegada,
        placa,
        origen,
        destino
    };

    let lista = JSON.parse(localStorage.getItem("traslados")) || [];
    lista.push(nuevoTraslado);
    localStorage.setItem("traslados", JSON.stringify(lista));

    mensaje.style.color = "green";
    mensaje.innerText = "Traslado guardado correctamente";

    document.getElementById("tipoDocumentoT").value = "";
    document.getElementById("documentoT").value = "";
    document.getElementById("nombreT").value = "";
    document.getElementById("apellidosT").value = "";
    document.getElementById("fechaT").value = "";
    document.getElementById("horaOrigen").value = "";
    document.getElementById("horaLlegada").value = "";
    document.getElementById("placa").value = "";
    document.getElementById("origenT").value = "";
    document.getElementById("destinoT").value = "";
}

function mostrarAgendamientos() {

    let lista = JSON.parse(localStorage.getItem("agendamientos")) || [];

    let tabla = document.getElementById("tablaAgendamientos");
    if (!tabla) return;

    tabla.innerHTML = "";

    lista.forEach((item, index) => {
        tabla.innerHTML += `
            <tr>
                <td>${index + 1}</td>
                <td>${item.tipoDocumento}</td>
                <td>${item.documento}</td>
                <td>${item.nombre}</td>
                <td>${item.apellidos}</td>
                <td>${item.origen}</td>
                <td>${item.destino}</td>
                <td>${item.fecha}</td>
                <td>${item.hora}</td>
            </tr>
        `;
    });
}

function mostrarTraslados() {

    let lista = JSON.parse(localStorage.getItem("traslados")) || [];

    let tabla = document.getElementById("tablaTraslados");
    if (!tabla) return;

    tabla.innerHTML = "";

    lista.forEach((item, index) => {
        tabla.innerHTML += `
            <tr>
               <td>${index + 1}</td>
                <td>${item.tipoDocumento}</td>
                <td>${item.documento}</td>
                <td>${item.nombre}</td>
                <td>${item.apellidos}</td>
                <td>${item.origen}</td>
                <td>${item.destino}</td>
                <td>${item.fecha}</td>
                <td>${item.horaOrigen}</td>
                <td>${item.horaLlegada}</td>
                <td>${item.placa}</td>
            </tr>
        `;
    });
}