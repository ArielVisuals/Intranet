"""URLs del portal: dashboard, avisos y directorio."""
from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("avisos/", views.avisos, name="avisos"),
    path("directorio/", views.directorio, name="directorio"),
]
