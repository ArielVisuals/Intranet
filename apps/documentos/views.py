"""
Vistas de la app 'documentos'.

Implementa:
1. Listado con aislamiento estricto de visibilidad por área.
2. Búsqueda por palabras clave y filtrado por categoría.
3. Carga de archivos con vinculación automática del área emisora.
4. Descarga segura y controlada mediante FileResponse verificando permisos en el servidor.
5. Eliminación de documentos reservada al propietario, jefe de área o administrador.
"""

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Documento, CategoriaDocumento, VisibilidadDocumento
from .forms import FormularioDocumento


@login_required
def lista_documentos(request):
    """
    Lista los documentos a los que el usuario tiene autorización de lectura.
    Permite búsqueda por texto y filtro por categoría.
    """
    usuario = request.user
    es_admin = usuario.is_superuser or usuario.groups.filter(name="Administrador").exists()

    # 1. Regla de visibilidad en el backend (Row-Level Security)
    if es_admin:
        # Los administradores pueden auditar y consultar todo el archivo digital
        documentos = Documento.objects.all()
    else:
        area_usuario = getattr(getattr(usuario, "perfil", None), "area", None)
        # Filtro: Toda la empresa O (Solo área Y coincide con el área del usuario)
        filtro_acceso = Q(visibilidad=VisibilidadDocumento.TODA_EMPRESA)
        if area_usuario:
            filtro_acceso |= Q(visibilidad=VisibilidadDocumento.SOLO_AREA, area=area_usuario)
        documentos = Documento.objects.filter(filtro_acceso)

    # 2. Búsqueda por término (título o descripción)
    termino_busqueda = request.GET.get("q", "").strip()
    if termino_busqueda:
        documentos = documentos.filter(
            Q(titulo__icontains=termino_busqueda) | Q(descripcion__icontains=termino_busqueda)
        )

    # 3. Filtro por categoría
    categoria_filtro = request.GET.get("categoria", "").strip()
    if categoria_filtro in CategoriaDocumento.values:
        documentos = documentos.filter(categoria=categoria_filtro)

    # Optimización SQL: select_related para traer en un solo JOIN el área y quien subió
    documentos = documentos.select_related("area", "subido_por")

    return render(request, "documentos/lista.html", {
        "documentos": documentos,
        "categorias": CategoriaDocumento.choices,
        "categoria_actual": categoria_filtro,
        "termino_busqueda": termino_busqueda,
        "total_documentos": documentos.count(),
    })


@login_required
def subir_documento(request):
    """
    Formulario para subir un nuevo documento corporativo.
    Asigna al usuario en sesión como autor y su área en caso de visibilidad restringida.
    """
    perfil = getattr(request.user, "perfil", None)

    if request.method == "POST":
        form = FormularioDocumento(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.subido_por = request.user

            # Si se marcó como exclusivo de área, se asocia al área del empleado
            if documento.visibilidad == VisibilidadDocumento.SOLO_AREA:
                if not perfil or not perfil.area:
                    messages.error(
                        request,
                        "No tienes un área asignada en tu perfil para restringir la visibilidad."
                    )
                    return render(request, "documentos/subir.html", {"form": form})
                documento.area = perfil.area

            documento.save()
            messages.success(request, f"Documento '{documento.titulo}' publicado exitosamente.")
            return redirect("documentos:lista")
    else:
        form = FormularioDocumento()

    return render(request, "documentos/subir.html", {
        "form": form,
        "area_usuario": getattr(perfil, "area", None),
    })


@login_required
def descargar_documento(request, pk):
    """
    Entrega el archivo binario validando previamente la visibilidad y permisos del usuario.
    Previene acceso no autorizado a documentos de otras áreas.
    """
    documento = get_object_or_404(Documento.objects.select_related("area"), pk=pk)

    # REGLA DE SEGURIDAD EN EL SERVIDOR:
    if not documento.puede_acceder(request.user):
        raise PermissionDenied("No cuentas con autorización para acceder a este documento.")

    try:
        # Abrimos el archivo en modo lectura binaria
        archivo_handle = documento.archivo.open("rb")
    except (FileNotFoundError, ValueError):
        raise Http404("El archivo solicitado no se encuentra disponible en el servidor.")

    # Obtenemos el nombre base limpio para la cabecera Content-Disposition
    nombre_descarga = os.path.basename(documento.archivo.name)

    # FileResponse transmite el archivo por streams (chunks) de forma eficiente
    # sin cargar todo el archivo en la memoria RAM del servidor.
    return FileResponse(archivo_handle, as_attachment=True, filename=nombre_descarga)


@login_required
@require_POST
def eliminar_documento(request, pk):
    """
    Permite eliminar un documento al creador original, jefe de área o administrador.
    """
    documento = get_object_or_404(Documento, pk=pk)
    usuario = request.user

    es_admin = usuario.is_superuser or usuario.groups.filter(name="Administrador").exists()
    es_propietario = documento.subido_por == usuario
    es_jefe_area = (
        usuario.groups.filter(name="Jefe de Área").exists()
        and getattr(usuario.perfil, "area", None) == documento.area
    )

    if not (es_admin or es_propietario or es_jefe_area):
        raise PermissionDenied("No tienes autorización para eliminar este documento.")

    titulo = documento.titulo
    # Borramos el archivo del disco
    if documento.archivo:
        documento.archivo.delete(save=False)
    documento.delete()

    messages.info(request, f"El documento '{titulo}' ha sido eliminado.")
    return redirect("documentos:lista")
