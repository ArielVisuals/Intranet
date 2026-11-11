"""
Modelos de la app 'portal'.

Define la cartelera de comunicados y avisos institucionales gestionados
por la administración para toda la comunidad de la organización.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class PrioridadAviso(models.TextChoices):
    """Niveles de prioridad para destacar comunicados en la intranet."""
    NORMAL = "normal", "Informativo"
    IMPORTANTE = "importante", "Importante"
    URGENTE = "urgente", "Urgente"


class Aviso(models.Model):
    """
    Comunicado oficial emitido por la dirección o administración de la empresa.
    """

    titulo = models.CharField(
        max_length=150,
        verbose_name="Título del aviso",
    )
    contenido = models.TextField(
        verbose_name="Contenido del comunicado",
    )
    prioridad = models.CharField(
        max_length=20,
        choices=PrioridadAviso.choices,
        default=PrioridadAviso.NORMAL,
        verbose_name="Prioridad",
    )
    publicado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="avisos_publicados",
        verbose_name="Publicado por",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Desmarcar para ocultar inmediatamente de la cartelera",
    )
    expira_en = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de caducidad",
        help_text="Opcional. Si se define, dejará de mostrarse después de esta fecha",
    )
    publicado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de publicación",
    )

    class Meta:
        verbose_name = "Aviso"
        verbose_name_plural = "Avisos"
        ordering = ["-publicado_en"]

    def __str__(self):
        return f"[{self.get_prioridad_display()}] {self.titulo}"

    @property
    def esta_vigente(self):
        """
        Calcula si el comunicado debe ser visible al público:
        debe estar marcado como activo y no haber superado su fecha de expiración.
        """
        if not self.activo:
            return False
        if self.expira_en and self.expira_en < timezone.now().date():
            return False
        return True

    @property
    def badge_prioridad(self):
        """Devuelve la clase CSS correspondiente para el badge de prioridad."""
        if self.prioridad == PrioridadAviso.URGENTE:
            return "badge-rechazada"  # Rojo de acento
        elif self.prioridad == PrioridadAviso.IMPORTANTE:
            return "badge-pendiente"  # Ámbar de advertencia
        return "badge-info"           # Azul informativo
