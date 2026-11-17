// ===== Menú en celular =====
const menuToggle = document.getElementById('menuToggle');
if (menuToggle) {
  menuToggle.addEventListener('click', () => {
    document.getElementById('menu').classList.toggle('abierto');
  });
}

// ===== Menú "Mi cuenta": abrir y cerrar con clic =====
const cuenta = document.querySelector('.cuenta');
if (cuenta) {
  cuenta.querySelector('.btn').addEventListener('click', (e) => {
    e.preventDefault();
    cuenta.classList.toggle('abierta');
  });
  document.addEventListener('click', (e) => {
    if (!cuenta.contains(e.target)) cuenta.classList.remove('abierta');
  });
}

// ===== Carrusel de novedades (solo en el inicio) =====
const slides = document.querySelectorAll('.slide');
const contenedorPuntos = document.getElementById('puntos');
if (slides.length && contenedorPuntos) {
  let actual = 0;

  slides.forEach((slide, i) => {
    const punto = document.createElement('button');
    punto.classList.add('punto');
    if (i === 0) punto.classList.add('activo');
    punto.addEventListener('click', () => mostrarSlide(i));
    contenedorPuntos.appendChild(punto);
  });
  const puntos = document.querySelectorAll('.punto');

  function mostrarSlide(indice) {
    slides[actual].classList.remove('activo');
    puntos[actual].classList.remove('activo');
    actual = (indice + slides.length) % slides.length;
    slides[actual].classList.add('activo');
    puntos[actual].classList.add('activo');
  }

  document.getElementById('siguiente').addEventListener('click', () => mostrarSlide(actual + 1));
  document.getElementById('anterior').addEventListener('click', () => mostrarSlide(actual - 1));
  setInterval(() => mostrarSlide(actual + 1), 4000);
}

// ===== Cambiar la foto de un insumo según el color (tarjetas del inicio) =====
document.querySelectorAll('.grid-insumos .tarjeta').forEach(tarjeta => {
  const foto = tarjeta.querySelector('.foto-insumo');
  tarjeta.querySelectorAll('.color').forEach(boton => {
    boton.addEventListener('click', () => {
      tarjeta.querySelectorAll('.color').forEach(b => b.classList.remove('activo'));
      boton.classList.add('activo');
      foto.src = boton.dataset.img;
    });
  });
});

// ===== Marcar vueltas tejidas con Fetch (sin recargar la página) =====
function leerCookie(nombre) {
  const valor = document.cookie.split('; ').find(c => c.startsWith(nombre + '='));
  return valor ? decodeURIComponent(valor.split('=')[1]) : '';
}

document.querySelectorAll('.check-vuelta').forEach(check => {
  check.addEventListener('change', async () => {
    const fila = check.closest('tr');
    try {
      const respuesta = await fetch(check.dataset.url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': leerCookie('csrftoken') },
        body: JSON.stringify({ completada: check.checked }),
      });
      if (!respuesta.ok) throw new Error('No se pudo guardar');
      const datos = await respuesta.json();

      fila.classList.toggle('hecha', check.checked);
      fila.classList.remove('actual');
      document.getElementById('porcentaje').textContent = datos.porcentaje + '%';
      document.getElementById('anillo').style.setProperty('--p', datos.porcentaje);
      document.getElementById('totalHechas').textContent = datos.total_hechas;
      document.getElementById('hechasPieza').textContent = datos.hechas_pieza;
    } catch (error) {
      check.checked = !check.checked;   // si falla, se deshace el cambio
      alert('No se pudo guardar tu progreso. Intenta de nuevo.');
    }
  });
});
