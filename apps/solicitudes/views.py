"""
Vistas de la app 'solicitudes'.

Maneja el flujo completo:
1. Listado filtrado según rol (Empleado: solo las suyas; Jefe: las de su área).
2. Creación con asignación automática de área y registro inicial de auditoría.
3. Detalle con validación de seguridad (403 si intenta ver una solicitud ajena).
4. Acciones de aprobación/rechazo por parte de la jefatura con comentario obligatorio.
5. Cancelación por parte del solicitante original.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Solicitud, HistorialSolicitud, EstadoSolicitud
from .forms import FormularioCrearSolicitud, FormularioAccionSolicitud


@login_required
def lista_solicitudes(request):
    """
    Lista las solicitudes accesibles para el usuario según su rol:
    - Empleado: estrictamente sus propias solicitudes.
    - Jefe de Área: por defecto las solicitudes de su área; puede alternar a ver las suyas.
    - Administrador: todas las solicitudes del sistema.
    """
    usuario = request.user
    es_admin = usuario.is_superuser or usuario.groups.filter(name="Administrador").exists()
    es_jefe_area = usuario.groups.filter(name="Jefe de Área").exists()

    # Parámetros de consulta (URL query params: ?vista=...&estado=...)
    vista = request.GET.get("vista", "area" if es_jefe_area else "mis_solicitudes")
    filtro_estado = request.GET.get("estado", "")

    # Base QuerySet según rol y vista seleccionada
    if es_admin:
        solicitudes = Solicitud.objects.all()
    elif es_jefe_area and vista == "area":
        # Filtra las solicitudes que pertenecen al área del jefe
        area_jefe = getattr(usuario.perfil, "area", None)
        if area_jefe:
            solicitudes = Solicitud.objects.filter(area=area_jefe)
        else:
            solicitudes = Solicitud.objects.none()
    else:
        # Empleado estándar (o jefe viendo sus propios trámites personales)
        solicitudes = Solicitud.objects.filter(solicitante=usuario)

    # Filtrado opcional por estado (pendiente, aprobada, rechazada)
    if filtro_estado in EstadoSolicitud.values:
        solicitudes = solicitudes.filter(estado=filtro_estado)

    # Optimización SQL: select_related hace un JOIN con solicitante y área
    # evitando el problema de N+1 consultas (como un eager load de un ORM).
    solicitudes = solicitudes.select_related("solicitante", "area")

    return render(request, "solicitudes/lista.html", {
        "solicitudes": solicitudes,
        "es_jefe_area": es_jefe_area,
        "es_admin": es_admin,
        "vista_actual": vista,
        "estado_actual": filtro_estado,
        "estados": EstadoSolicitud.choices,
    })


@login_required
def crear_solicitud(request):
    """
    Permite al empleado crear una nueva solicitud.
    Asigna automáticamente el solicitante y el área del usuario en sesión.
    """
    perfil = getattr(request.user, "perfil", None)
    if not perfil or not perfil.area:
        messages.error(
            request,
            "Tu usuario no tiene un Área asignada. Contacta al administrador antes de crear solicitudes.",
        )
        return redirect("solicitudes:lista")

    if request.method == "POST":
        form = FormularioCrearSolicitud(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.solicitante = request.user
            solicitud.area = perfil.area
            solicitud.estado = EstadoSolicitud.PENDIENTE
            solicitud.save()

            # Registro de auditoría inicial (trazabilidad)
            HistorialSolicitud.objects.create(
                solicitud=solicitud,
                usuario=request.user,
                estado_anterior=EstadoSolicitud.PENDIENTE,
                estado_nuevo=EstadoSolicitud.PENDIENTE,
                comentario="Solicitud creada y enviada a revisión.",
            )

            messages.success(request, "Tu solicitud ha sido enviada correctamente.")
            return redirect("solicitudes:detalle", pk=solicitud.pk)
    else:
        form = FormularioCrearSolicitud()

    return render(request, "solicitudes/crear.html", {
        "form": form,
        "area_usuario": perfil.area,
    })


@login_required
def detalle_solicitud(request, pk):
    """
    Muestra el detalle de una solicitud, su estado actual y el historial completo.
    Aplica regla estricta de autorización: 403 si el usuario no tiene permiso.
    """
    solicitud = get_object_or_404(
        Solicitud.objects.select_related("solicitante", "area"),
        pk=pk,
    )

    usuario = request.user
    es_admin = usuario.is_superuser or usuario.groups.filter(name="Administrador").exists()
    es_jefe_del_area = (
        usuario.groups.filter(name="Jefe de Área").exists()
        and (solicitud.area.jefe == usuario or getattr(usuario.perfil, "area", None) == solicitud.area)
    )
    es_propietario = solicitud.solicitante == usuario

    # REGLA DE SEGURIDAD EN EL SERVIDOR:
    # Solo el creador, el jefe del área responsable o el administrador pueden verla.
    if not (es_propietario or es_jefe_del_area or es_admin):
        raise PermissionDenied("No tienes autorización para consultar esta solicitud.")

    # Formulario para que el jefe o admin pueda aprobar/rechazar
    form_accion = FormularioAccionSolicitud() if solicitud.puede_gestionar(usuario) else None

    # Historial de cambios ordenado cronológicamente
    historial = solicitud.historial.select_related("usuario").all()

    return render(request, "solicitudes/detalle.html", {
        "solicitud": solicitud,
        "historial": historial,
        "puede_gestionar": solicitud.puede_gestionar(usuario),
        "puede_cancelar": solicitud.puede_cancelar(usuario),
        "form_accion": form_accion,
    })


@login_required
@require_POST
def gestionar_solicitud(request, pk):
    """
    Procesa la aprobación o rechazo de una solicitud.
    Solo puede ser ejecutada por el jefe de área correspondiente o admin.
    """
    solicitud = get_object_or_404(Solicitud, pk=pk)

    if not solicitud.puede_gestionar(request.user):
        raise PermissionDenied("No tienes permiso para aprobar o rechazar esta solicitud.")

    form = FormularioAccionSolicitud(request.POST)
    if form.is_valid():
        nueva_accion = form.cleaned_data["accion"]
        comentario = form.cleaned_data["comentario"]

        estado_anterior = solicitud.estado
        solicitud.estado = nueva_accion
        solicitud.save()

        # Guardamos el cambio en la tabla de auditoría inmutable
        HistorialSolicitud.objects.create(
            solicitud=solicitud,
            usuario=request.user,
            estado_anterior=estado_anterior,
            estado_nuevo=nueva_accion,
            comentario=comentario,
        )

        nombre_accion = "aprobada" if nueva_accion == EstadoSolicitud.APROBADA else "rechazada"
        messages.success(request, f"La solicitud ha sido {nombre_accion} exitosamente.")
    else:
        # Si hubo un error (por ejemplo, rechazar sin justificación)
        for error in form.errors.values():
            messages.error(request, error)

    return redirect("solicitudes:detalle", pk=solicitud.pk)


@login_required
@require_POST
def cancelar_solicitud(request, pk):
    """
    Permite al solicitante cancelar su propia solicitud pendiente.
    """
    solicitud = get_object_or_404(Solicitud, pk=pk)

    if not solicitud.puede_cancelar(request.user):
        raise PermissionDenied("No puedes cancelar esta solicitud.")

    estado_anterior = solicitud.estado
    solicitud.estado = EstadoSolicitud.CANCELADA
    solicitud.save()

    HistorialSolicitud.objects.create(
        solicitud=solicitud,
        usuario=request.user,
        estado_anterior=estado_anterior,
        estado_nuevo=EstadoSolicitud.CANCELADA,
        comentario="Solicitud cancelada directamente por el solicitante.",
    )

    messages.info(request, "Has cancelado la solicitud.")
    return redirect("solicitudes:detalle", pk=solicitud.pk)
