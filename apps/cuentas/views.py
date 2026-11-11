"""
Vistas de la app 'cuentas': login, logout y perfil de usuario.

Una vista en Django es una función (o clase) que recibe un objeto 'request'
y devuelve un objeto 'response' con HTML. Es exactamente como un endpoint
en una API de Express.js, pero en lugar de JSON devuelve HTML renderizado.

Estrategia:
- Login/logout: usamos las vistas genéricas de Django (LoginView, LogoutView)
  porque ya manejan correctamente CSRF, sesiones y redirecciones.
- Perfil: vista propia (function-based view) porque la lógica es específica.

Function-based views (FBV) vs Class-based views (CBV):
  Usamos FBV porque son más fáciles de leer — el código fluye de arriba a abajo
  sin magia heredada. Para un entrevistador junior, es más fácil de explicar.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib import messages
from .forms import FormularioLogin, FormularioPerfil


class VistaLogin(DjangoLoginView):
    """
    Extiende la LoginView de Django para usar nuestro formulario y plantilla.

    DjangoLoginView ya maneja:
    - Validación de credenciales
    - Creación de sesión
    - Protección CSRF
    - Redirección post-login (a LOGIN_REDIRECT_URL de settings.py)

    Nosotros solo añadimos: nuestra plantilla y nuestro formulario con estilos.
    """

    template_name = "cuentas/login.html"
    form_class = FormularioLogin
    redirect_authenticated_user = True  # Si ya tiene sesión, redirige al dashboard

    def get_context_data(self, **kwargs):
        """
        Agrega datos extra al contexto de la plantilla.
        'context' es el diccionario que Django pasa al template,
        equivale a las props en React.
        """
        context = super().get_context_data(**kwargs)
        context["titulo_pagina"] = "Iniciar sesión"
        return context


@login_required  # Si no hay sesión, redirige a LOGIN_URL (definido en settings.py)
def vista_perfil(request):
    """
    Muestra y procesa el formulario de perfil del usuario actual.

    Patrón GET/POST:
    - GET: muestra el formulario con los datos actuales
    - POST: valida y guarda los nuevos datos

    Este patrón es exactamente como manejarías un formulario en Express.js:
    if (req.method === 'POST') { procesar } else { mostrar formulario }
    """
    # request.user.perfil accede al PerfilUsuario gracias al related_name="perfil"
    # que definimos con OneToOneField en el modelo.
    perfil = request.user.perfil

    if request.method == "POST":
        formulario = FormularioPerfil(request.POST, instance=perfil)
        if formulario.is_valid():
            formulario.save()
            # messages.success agrega un mensaje flash que base.html mostrará
            # automáticamente en la siguiente petición (como un toast en React)
            messages.success(request, "Tu perfil ha sido actualizado correctamente.")
            return redirect("cuentas:perfil")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        formulario = FormularioPerfil(instance=perfil)

    return render(request, "cuentas/perfil.html", {
        "formulario": formulario,
        "perfil": perfil,
    })
