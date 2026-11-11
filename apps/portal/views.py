"""
Vistas del portal: dashboard, avisos y directorio.
En esta fase solo son placeholders funcionales.
Se completarán con toda la lógica en la Fase 5.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


@login_required
def dashboard(request):
    """Vista principal del portal. Muestra un resumen según el rol del usuario."""
    return render(request, "portal/dashboard.html", {
        "titulo": "Inicio",
    })


@login_required
def avisos(request):
    """Cartelera de avisos corporativos. Se completará en Fase 5."""
    return render(request, "portal/avisos.html", {
        "titulo": "Avisos",
        "avisos": [],  # Placeholder vacío hasta Fase 5
    })


@login_required
def directorio(request):
    """Directorio de empleados con búsqueda. Se completará en Fase 5."""
    return render(request, "portal/directorio.html", {
        "titulo": "Directorio",
        "empleados": [],  # Placeholder vacío hasta Fase 5
    })
