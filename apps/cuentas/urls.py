"""
URLs de la app 'cuentas'.

app_name define el 'namespace' de estas URLs, que se usa para referenciarlas
sin hardcodear la ruta. Por ejemplo, {% url 'cuentas:login' %} en una
plantilla, o reverse('cuentas:logout') en Python. Es como los named routes
en React Router o Vue Router.
"""

from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = "cuentas"

urlpatterns = [
    # Login: nuestra vista personalizada que extiende la de Django
    path("login/", views.VistaLogin.as_view(), name="login"),

    # Logout: usamos directamente la LogoutView de Django.
    # Solo acepta POST (desde Django 5+) para protección CSRF.
    # next_page indica a dónde redirigir después del logout.
    path("logout/", LogoutView.as_view(next_page="cuentas:login"), name="logout"),

    # Perfil del usuario actual
    path("perfil/", views.vista_perfil, name="perfil"),
]
