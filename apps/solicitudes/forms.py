"""
Formularios para el módulo de solicitudes.

En Django, clean() realiza la validación cruzada entre múltiples campos
(por ejemplo, verificar que fecha_fin sea posterior a fecha_inicio),
equivalente a un .refine() en Zod de JavaScript o validaciones en un onSubmit.
"""

from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .models import Solicitud, TipoSolicitud, EstadoSolicitud


class FormularioCrearSolicitud(forms.ModelForm):
    """
    Formulario para que un empleado redacte y envíe una nueva solicitud.
    """

    class Meta:
        model = Solicitud
        fields = ["tipo", "asunto", "descripcion", "fecha_inicio", "fecha_fin"]
        labels = {
            "tipo": "Tipo de solicitud",
            "asunto": "Asunto",
            "descripcion": "Descripción detallada",
            "fecha_inicio": "Fecha de inicio",
            "fecha_fin": "Fecha de término",
        }
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "asunto": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. Solicitud de vacaciones periodo de verano",
            }),
            "descripcion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Detalla el motivo, justificación o requerimiento...",
            }),
            "fecha_inicio": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "fecha_fin": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
        }

    def clean(self):
        """
        Validación de reglas de negocio:
        1. Para vacaciones y permisos, las fechas son obligatorias.
        2. La fecha de fin no puede ser anterior a la de inicio.
        """
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        if tipo in [TipoSolicitud.VACACIONES, TipoSolicitud.PERMISO]:
            if not fecha_inicio:
                self.add_error("fecha_inicio", "La fecha de inicio es requerida para este tipo de solicitud.")
            if not fecha_fin:
                self.add_error("fecha_fin", "La fecha de término es requerida para este tipo de solicitud.")

        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                self.add_error("fecha_fin", "La fecha de término no puede ser anterior a la fecha de inicio.")

        return cleaned_data


class FormularioAccionSolicitud(forms.Form):
    """
    Formulario utilizado por Jefes de Área o Administradores para aprobar o rechazar.
    Exige comentario obligatorio en caso de rechazo.
    """

    accion = forms.ChoiceField(
        choices=[
            (EstadoSolicitud.APROBADA, "Aprobar"),
            (EstadoSolicitud.RECHAZADA, "Rechazar"),
        ],
        widget=forms.HiddenInput(),
    )
    comentario = forms.CharField(
        required=False,
        label="Comentario o retroalimentación",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Ingresa una justificación o comentario para el solicitante...",
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        accion = cleaned_data.get("accion")
        comentario = (cleaned_data.get("comentario") or "").strip()

        # Al rechazar, la política corporativa exige documentar el motivo
        if accion == EstadoSolicitud.RECHAZADA and not comentario:
            self.add_error("comentario", "Debes ingresar un comentario justificando el motivo del rechazo.")

        return cleaned_data
