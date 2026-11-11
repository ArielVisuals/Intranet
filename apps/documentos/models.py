"""
Modelos de la app 'documentos'.

Permite la gestión, categorización y control de visibilidad de archivos
digitales corporativos (políticas, manuales y formatos).

En SQL:
- Tabla con llaves foráneas a auth_user (subido_por) y area (área de restricción).
- Guarda la ruta relativa del archivo en el sistema de almacenamiento.
"""

import os
from django.db import models
from django.contrib.auth.models import User
from apps.cuentas.models import Area


class CategoriaDocumento(models.TextChoices):
    """Categorías principales de documentación corporativa."""
    POLITICAS = "politicas", "Políticas y Normativas"
    FORMATOS = "formatos", "Formatos y Plantillas"
    MANUALES = "manuales", "Manuales y Guías"


class VisibilidadDocumento(models.TextChoices):
    """Ámbito de visibilidad del documento."""
    TODA_EMPRESA = "toda_empresa", "Toda la empresa"
    SOLO_AREA = "solo_area", "Solo para mi área"


def ruta_archivo_documento(instance, filename):
    """
    Función que genera una ruta de guardado organizada por año y mes.
    Ejemplo: media/documentos/2026/11/manual_calidad.pdf
    """
    return f"documentos/{instance.categoria}/{filename}"


class Documento(models.Model):
    """
    Representa un archivo corporativo alojado en la intranet.
    """

    titulo = models.CharField(
        max_length=150,
        verbose_name="Título del documento",
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción",
        help_text="Resumen del contenido o instrucciones de uso",
    )
    categoria = models.CharField(
        max_length=20,
        choices=CategoriaDocumento.choices,
        default=CategoriaDocumento.POLITICAS,
        verbose_name="Categoría",
    )
    archivo = models.FileField(
        upload_to=ruta_archivo_documento,
        verbose_name="Archivo digital",
    )
    visibilidad = models.CharField(
        max_length=20,
        choices=VisibilidadDocumento.choices,
        default=VisibilidadDocumento.TODA_EMPRESA,
        verbose_name="Visibilidad",
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos",
        verbose_name="Área con acceso",
        help_text="Requerido si la visibilidad es 'Solo para mi área'",
    )
    subido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="documentos_subidos",
        verbose_name="Subido por",
    )
    tamanio_bytes = models.BigIntegerField(
        default=0,
        verbose_name="Tamaño en bytes",
    )
    subido_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de publicación",
    )

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["-subido_en"]

    def __str__(self):
        return f"{self.titulo} ({self.get_categoria_display()})"

    def save(self, *args, **kwargs):
        """
        Calcula y guarda automáticamente el tamaño del archivo en bytes
        antes de registrarlo en la base de datos.
        """
        if self.archivo and hasattr(self.archivo, "size"):
            self.tamanio_bytes = self.archivo.size
        super().save(*args, **kwargs)

    @property
    def extension(self):
        """Obtiene la extensión del archivo en minúsculas (ej: .pdf)."""
        if self.archivo:
            _, ext = os.path.splitext(self.archivo.name)
            return ext.lower()
        return ""

    @property
    def tamanio_legible(self):
        """
        Convierte los bytes a formato humano legible (KB o MB).
        Equivale a una función utilitaria formatBytes() en JavaScript.
        """
        bytes_val = self.tamanio_bytes or 0
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.1f} KB"
        else:
            return f"{bytes_val / (1024 * 1024):.2f} MB"

    @property
    def icono_bootstrap(self):
        """
        Retorna la clase de icono de Bootstrap Icons apropiada según la extensión.
        """
        ext = self.extension
        if ext == ".pdf":
            return "bi-file-earmark-pdf text-danger"
        elif ext in [".xlsx", ".xls", ".csv"]:
            return "bi-file-earmark-excel text-success"
        elif ext in [".docx", ".doc"]:
            return "bi-file-earmark-word text-info"
        elif ext in [".pptx", ".ppt"]:
            return "bi-file-earmark-ppt"
        elif ext in [".jpg", ".jpeg", ".png"]:
            return "bi-file-earmark-image"
        return "bi-file-earmark-text"

    def puede_acceder(self, usuario):
        """
        Regla de autorización:
        - Si el documento es para toda la empresa: acceso libre a todo autenticado.
        - Si es solo para un área: solo empleados de esa área o administradores.
        """
        if not usuario.is_authenticated:
            return False

        if usuario.is_superuser or usuario.groups.filter(name="Administrador").exists():
            return True

        if self.visibilidad == VisibilidadDocumento.TODA_EMPRESA:
            return True

        # Si es 'solo_area', verificamos que el usuario pertenezca a dicha área
        perfil = getattr(usuario, "perfil", None)
        return bool(perfil and perfil.area and perfil.area == self.area)
