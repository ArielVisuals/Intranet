"""
Vistas de solicitudes — placeholder hasta Fase 3.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def lista_solicitudes(request):
    return render(request, "solicitudes/lista.html", {"titulo": "Solicitudes"})
