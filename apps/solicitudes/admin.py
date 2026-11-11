"""
Configuración del panel de administración para la app 'solicitudes'.

Incluye la pista de auditoría (HistorialSolicitud) como un inline de solo lectura
para que el Administrador tenga trazabilidad sin poder alterar los registros históricos.
"""

from django.contrib import admin
from .models import Solicitud, HistorialSolicitud


class HistorialSolicitudInline(admin.TabularInline):
    """
    Muestra el historial de cambios en formato de tabla dentro de la solicitud.
    Los campos son de solo lectura para preservar la integridad de la auditoría.
    """
    model = HistorialSolicitud
    extra = 0
    can_delete = False
    readonly_fields = ["usuario", "estado_anterior", "estado_nuevo", "comentario", "fecha"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ["id", "asunto", "tipo", "solicitante", "area", "estado", "creado_en"]
    list_filter = ["estado", "tipo", "area", "creado_en"]
    search_fields = ["asunto", "descripcion", "solicitante__username", "solicitante__first_name", "solicitante__last_name"]
    readonly_fields = ["creado_en", "actualizado_en"]
    inlines = [HistorialSolicitudInline]

    fieldsets = [
        ("Datos principales", {
            "fields": ["solicitante", "area", "tipo", "estado"],
        }),
        ("Contenido", {
            "fields": ["asunto", "descripcion"],
        }),
        ("Vigencia / Fechas", {
            "fields": ["fecha_inicio", "fecha_fin"],
        }),
        ("Metadatos del sistema", {
            "fields": ["creado_en", "actualizado_en"],
            "classes": ["collapse"],
        }),
    ]


@admin.register(HistorialSolicitud)
class HistorialSolicitudAdmin(admin.ModelAdmin):
    list_display = ["solicitud", "usuario", "estado_anterior", "estado_nuevo", "fecha"]
    list_filter = ["estado_anterior", "estado_nuevo", "fecha"]
    search_fields = ["solicitud__asunto", "usuario__username", "comentario"]
    readonly_fields = ["solicitud", "usuario", "estado_anterior", "estado_nuevo", "comentario", "fecha"]

    def has_add_permission(self, request):
        # El historial solo se genera por código ante transiciones de estado
        return False

    def has_delete_permission(self, request, obj=None):
        # Inmutable
        return False
