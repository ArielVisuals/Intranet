/**
 * portal.js — JavaScript ligero para el Portal Universidad
 *
 * No usamos React ni ningún framework. Este archivo maneja pequeñas
 * interacciones del lado del cliente: cerrar mensajes flash, menú móvil,
 * confirmaciones de acción peligrosa, etc.
 *
 * "DOMContentLoaded" equivale al useEffect(() => {}, []) de React:
 * se ejecuta una sola vez cuando el HTML ya está cargado.
 */

document.addEventListener('DOMContentLoaded', function () {

  // --- Auto-cierre de mensajes flash ---
  // Los mensajes de éxito/error desaparecen después de 5 segundos.
  const flashMessages = document.querySelectorAll('.flash-message');
  flashMessages.forEach(function (msg) {
    // Auto-cierre después de 5 segundos
    setTimeout(function () {
      msg.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      msg.style.opacity = '0';
      msg.style.transform = 'translateX(20px)';
      setTimeout(function () { msg.remove(); }, 400);
    }, 5000);
  });

  // Cierre manual al hacer clic en el botón "×"
  document.querySelectorAll('.flash-close').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const msg = btn.closest('.flash-message');
      msg.style.transition = 'opacity 0.3s ease';
      msg.style.opacity = '0';
      setTimeout(function () { msg.remove(); }, 300);
    });
  });

  // --- Menú móvil ---
  // El botón hamburguesa muestra/oculta la navegación en pantallas pequeñas.
  const toggle = document.getElementById('navbar-toggle');
  const navMenu = document.getElementById('navbar-menu');
  if (toggle && navMenu) {
    toggle.addEventListener('click', function () {
      const isOpen = navMenu.classList.toggle('mobile-open');
      toggle.setAttribute('aria-expanded', isOpen);
    });
    // Cierra el menú al hacer clic en cualquier link dentro de él
    navMenu.querySelectorAll('.nav-link').forEach(function (link) {
      link.addEventListener('click', function () {
        navMenu.classList.remove('mobile-open');
      });
    });
  }

  // --- Confirmación en acciones destructivas ---
  // Cualquier elemento con data-confirm="mensaje" pedirá confirmación.
  // Equivale a un window.confirm() antes de un fetch DELETE en React.
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      const message = el.getAttribute('data-confirm');
      if (!window.confirm(message)) {
        e.preventDefault();
      }
    });
  });

  // --- Resaltar fila de tabla al hacer clic (si tiene enlace) ---
  document.querySelectorAll('tr[data-href]').forEach(function (row) {
    row.style.cursor = 'pointer';
    row.addEventListener('click', function () {
      window.location.href = row.getAttribute('data-href');
    });
  });

});
