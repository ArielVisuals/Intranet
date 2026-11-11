"""
Vistas de documentos — placeholder hasta Fase 4.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def lista_documentos(request):
    return render(request, "documentos/lista.html", {"titulo": "Documentos"})
