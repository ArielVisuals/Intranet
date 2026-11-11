"""
Configuración del panel de administración para la app 'documentos'.
"""

from django.contrib import admin
from .models import Documento


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ["titulo", "categoria", "visibilidad", "area", "subido_por", "tamanio_formato", "subido_en"]
    list_filter = ["categoria", "visibilidad", "area", "subido_en"]
    search_fields = ["titulo", "descripcion", "subido_por__username"]
    readonly_fields = ["tamanio_bytes", "subido_en"]

    fieldsets = [
        ("Información del documento", {
            "fields": ["titulo", "descripcion", "categoria", "archivo"],
        }),
        ("Privacidad y visibilidad", {
            "fields": ["visibilidad", "area"],
        }),
        ("Metadatos", {
            "fields": ["subido_por", "tamanio_bytes", "subido_en"],
            "classes": ["collapse"],
        }),
    ]

    def tamanio_formato(self, obj):
        return obj.tamanio_legible
    tamanio_formato.short_description = "Tamaño"
