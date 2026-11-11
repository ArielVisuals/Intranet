"""
URLs del módulo de solicitudes.
"""

from django.urls import path
from . import views

app_name = "solicitudes"

urlpatterns = [
    path("", views.lista_solicitudes, name="lista"),
    path("crear/", views.crear_solicitud, name="crear"),
    path("<int:pk>/", views.detalle_solicitud, name="detalle"),
    path("<int:pk>/gestionar/", views.gestionar_solicitud, name="gestionar"),
    path("<int:pk>/cancelar/", views.cancelar_solicitud, name="cancelar"),
]
