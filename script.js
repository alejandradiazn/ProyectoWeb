// ===== Carrusel de novedades =====
const slides = document.querySelectorAll('.slide');
const contenedorPuntos = document.getElementById('puntos');
let actual = 0;

// Crear un punto por cada slide
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

// Cambio automático cada 4 segundos
setInterval(() => mostrarSlide(actual + 1), 4000);

// ===== Menú en celular =====
document.getElementById('menuToggle').addEventListener('click', () => {
  document.getElementById('menu').classList.toggle('abierto');
});

// ===== Cambiar foto de la lana chenille según el color =====
const fotoChenille = document.getElementById('fotoChenille');
document.querySelectorAll('.color').forEach(boton => {
  boton.addEventListener('click', () => {
    document.querySelectorAll('.color').forEach(b => b.classList.remove('activo'));
    boton.classList.add('activo');
    fotoChenille.src = boton.dataset.img;
  });
});
