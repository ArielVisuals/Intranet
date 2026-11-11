"""
Modelos de la app 'solicitudes'.

Representa las solicitudes de los empleados (vacaciones, permisos, soporte TI)
y su pista de auditoría (historial de cambios de estado).

En SQL:
- Solicitud equivale a una tabla con llaves foráneas a auth_user y area.
- HistorialSolicitud es una tabla hija (relación 1 a muchos) que registra
  cada cambio de estado para garantizar la trazabilidad corporativa.
"""

from django.db import models
from django.contrib.auth.models import User
from apps.cuentas.models import Area


class TipoSolicitud(models.TextChoices):
    """
    Enumeración de tipos de solicitud permitidos.
    TextChoices de Django genera internamente una restricción CHECK en SQL
    asegurando que solo se almacenen valores válidos.
    """
    VACACIONES = "vacaciones", "Vacaciones"
    PERMISO = "permiso", "Permiso laboral"
    SOPORTE_TI = "soporte_ti", "Soporte de TI"


class EstadoSolicitud(models.TextChoices):
    """
    Estados posibles dentro del ciclo de vida de una solicitud.
    """
    PENDIENTE = "pendiente", "Pendiente"
    APROBADA = "aprobada", "Aprobada"
    RECHAZADA = "rechazada", "Rechazada"
    CANCELADA = "cancelada", "Cancelada"


class Solicitud(models.Model):
    """
    Solicitud creada por un empleado para aprobación de su jefatura o atención de TI.
    """

    solicitante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="solicitudes_creadas",
        verbose_name="Solicitante",
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,  # Evita borrar el área si tiene solicitudes históricas
        related_name="solicitudes",
        verbose_name="Área",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoSolicitud.choices,
        default=TipoSolicitud.PERMISO,
        verbose_name="Tipo de solicitud",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoSolicitud.choices,
        default=EstadoSolicitud.PENDIENTE,
        verbose_name="Estado actual",
    )
    asunto = models.CharField(
        max_length=150,
        verbose_name="Asunto",
        help_text="Resumen breve del motivo de la solicitud",
    )
    descripcion = models.TextField(
        verbose_name="Descripción detallada",
        help_text="Explica los detalles o justificación de tu solicitud",
    )
    fecha_inicio = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de inicio",
        help_text="Requerido para permisos y vacaciones",
    )
    fecha_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de término",
        help_text="Requerido para permisos y vacaciones",
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    class Meta:
        verbose_name = "Solicitud"
        verbose_name_plural = "Solicitudes"
        ordering = ["-creado_en"]  # Más recientes primero

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.asunto} - {self.solicitante.username}"

    def puede_cancelar(self, usuario):
        """Un empleado solo puede cancelar su propia solicitud si está pendiente."""
        return self.solicitante == usuario and self.estado == EstadoSolicitud.PENDIENTE

    def puede_gestionar(self, usuario):
        """
        Un usuario puede aprobar o rechazar si:
        1. Es superusuario o Administrador.
        2. Es el jefe asignado del área a la que pertenece la solicitud,
           o pertenece al grupo 'Jefe de Área' de esa misma área.
        Y la solicitud está actualmente en estado 'pendiente'.
        """
        if self.estado != EstadoSolicitud.PENDIENTE:
            return False

        if usuario.is_superuser or usuario.groups.filter(name="Administrador").exists():
            return True

        if usuario.groups.filter(name="Jefe de Área").exists():
            # Si el área tiene un jefe explícito asignado
            if self.area.jefe == usuario:
                return True
            # O si el perfil del jefe coincide con el área de la solicitud
            if hasattr(usuario, "perfil") and usuario.perfil.area == self.area:
                return True

        return False


class HistorialSolicitud(models.Model):
    """
    Registro inmutable de cada cambio de estado en una solicitud.
    Garantiza la trazabilidad (quién aprobó/rechazó, cuándo y el motivo).
    """

    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name="historial",
        verbose_name="Solicitud",
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Usuario responsable",
    )
    estado_anterior = models.CharField(
        max_length=20,
        choices=EstadoSolicitud.choices,
        verbose_name="Estado anterior",
    )
    estado_nuevo = models.CharField(
        max_length=20,
        choices=EstadoSolicitud.choices,
        verbose_name="Estado nuevo",
    )
    comentario = models.TextField(
        blank=True,
        verbose_name="Comentario o justificación",
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y hora de acción",
    )

    class Meta:
        verbose_name = "Historial de solicitud"
        verbose_name_plural = "Historiales de solicitudes"
        ordering = ["fecha"]  # Orden cronológico para la línea de tiempo

    def __str__(self):
        return f"{self.solicitud.id}: {self.estado_anterior} -> {self.estado_nuevo} ({self.fecha:%d/%m/%Y %H:%M})"
