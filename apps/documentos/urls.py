"""URLs de documentos — placeholder hasta Fase 4."""
from django.urls import path
from . import views

app_name = "documentos"

urlpatterns = [
    path("", views.lista_documentos, name="lista"),
]
