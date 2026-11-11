"""
URLs del módulo de documentos.
"""

from django.urls import path
from . import views

app_name = "documentos"

urlpatterns = [
    path("", views.lista_documentos, name="lista"),
    path("subir/", views.subir_documento, name="subir"),
    path("<int:pk>/descargar/", views.descargar_documento, name="descargar"),
    path("<int:pk>/eliminar/", views.eliminar_documento, name="eliminar"),
]
