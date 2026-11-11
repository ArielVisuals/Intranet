"""
Formularios para la app 'documentos'.

Implementa validaciones estrictas de tamaño y tipo MIME / extensión para
prevenir la carga de archivos maliciosos (ejecutables, scripts, etc.)
o sobrecarga de almacenamiento.
"""

import os
from django import forms
from django.core.exceptions import ValidationError
from .models import Documento, VisibilidadDocumento

# Extensiones autorizadas por la política de seguridad corporativa
EXTENSIONES_PERMITIDAS = [
    ".pdf",
    ".docx", ".doc",
    ".xlsx", ".xls", ".csv",
    ".pptx", ".ppt",
    ".txt",
    ".jpg", ".jpeg", ".png",
]

# Límite máximo: 10 Megabytes
LIMITE_TAMANIO_BYTES = 10 * 1024 * 1024


class FormularioDocumento(forms.ModelForm):
    """
    Formulario para la carga de nuevos documentos corporativos.
    """

    class Meta:
        model = Documento
        fields = ["titulo", "descripcion", "categoria", "visibilidad", "archivo"]
        labels = {
            "titulo": "Título del documento",
            "descripcion": "Descripción o instrucciones",
            "categoria": "Categoría",
            "visibilidad": "Ámbito de visibilidad",
            "archivo": "Seleccionar archivo",
        }
        widgets = {
            "titulo": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. Política de Viáticos y Reembolsos 2026",
            }),
            "descripcion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Breve explicación de la finalidad del documento...",
            }),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "visibilidad": forms.Select(attrs={"class": "form-select"}),
            "archivo": forms.FileInput(attrs={"class": "form-control"}),
        }

    def clean_archivo(self):
        """
        Valida que el archivo cumpla con las extensiones permitidas
        y que no exceda el límite de 10 MB.
        """
        archivo = self.cleaned_data.get("archivo")
        if not archivo:
            raise ValidationError("Debes adjuntar un archivo.")

        # 1. Validar extensión
        nombre = archivo.name
        _, ext = os.path.splitext(nombre)
        ext_lower = ext.lower()

        if ext_lower not in EXTENSIONES_PERMITIDAS:
            permitidas_str = ", ".join(EXTENSIONES_PERMITIDAS)
            raise ValidationError(
                f"Formato no permitido ({ext_lower}). Formatos admitidos: {permitidas_str}"
            )

        # 2. Validar tamaño máximo
        if archivo.size > LIMITE_TAMANIO_BYTES:
            tamanio_mb = archivo.size / (1024 * 1024)
            raise ValidationError(
                f"El archivo pesa {tamanio_mb:.1f} MB, excediendo el límite de 10 MB permitido."
            )

        return archivo
