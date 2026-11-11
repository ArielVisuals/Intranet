"""URLs de solicitudes — placeholder hasta Fase 3."""
from django.urls import path
from . import views

app_name = "solicitudes"

urlpatterns = [
    path("", views.lista_solicitudes, name="lista"),
]
