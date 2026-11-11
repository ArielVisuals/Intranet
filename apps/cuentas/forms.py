"""
Formularios de la app 'cuentas'.

En Django, un formulario es una clase Python que:
1. Define los campos y sus validaciones
2. Renderiza el HTML del formulario (opcional, podemos hacer el HTML manual)
3. Valida los datos enviados por el usuario

Es similar a usar Zod o Yup en React para validación, pero integrado
con la generación del HTML.

Usamos el AuthenticationForm de Django para el login porque ya implementa:
- Validación de usuario/contraseña contra la base de datos
- Protección contra enumeración de usuarios
- Mensajes de error en español (con LANGUAGE_CODE = 'es-mx')
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import PerfilUsuario


class FormularioLogin(AuthenticationForm):
    """
    Extiende el AuthenticationForm de Django para agregar clases CSS
    de nuestro sistema de diseño. No cambiamos la lógica de autenticación,
    solo la presentación.

    En React harías esto con className en el JSX.
    En Django Forms se hace en el atributo 'widget' de cada campo.
    """

    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Nombre de usuario",
            "autocomplete": "username",
            "autofocus": True,
        }),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Contraseña",
            "autocomplete": "current-password",
        }),
    )


class FormularioPerfil(forms.ModelForm):
    """
    Formulario para que el usuario edite su perfil.

    ModelForm es un formulario vinculado a un modelo: genera automáticamente
    los campos a partir del modelo, equivale a un formulario controlado en
    React que sincroniza estado con la base de datos.
    """

    # Campos del modelo User (nombre, apellido, email)
    # Los incluimos manualmente porque están en el User, no en PerfilUsuario.
    nombre = forms.CharField(
        label="Nombre",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    apellido = forms.CharField(
        label="Apellido",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = PerfilUsuario
        fields = ["telefono", "puesto", "fecha_ingreso"]
        labels = {
            "telefono": "Teléfono",
            "puesto": "Puesto",
            "fecha_ingreso": "Fecha de ingreso",
        }
        widgets = {
            "telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "55 1234 5678"}),
            "puesto": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Analista de Sistemas"}),
            "fecha_ingreso": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Precarga los campos del User (nombre, apellido, email) en el formulario.
        'instance' es el PerfilUsuario actual; accedemos al User con instance.usuario.
        """
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            usuario = self.instance.usuario
            self.fields["nombre"].initial = usuario.first_name
            self.fields["apellido"].initial = usuario.last_name
            self.fields["email"].initial = usuario.email

    def save(self, commit=True):
        """
        Guarda el perfil Y actualiza los campos del User al mismo tiempo.
        Sobrescribimos save() para manejar los dos modelos (User + PerfilUsuario).
        """
        perfil = super().save(commit=False)
        # Actualizar campos del User directamente
        usuario = perfil.usuario
        usuario.first_name = self.cleaned_data.get("nombre", "")
        usuario.last_name = self.cleaned_data.get("apellido", "")
        usuario.email = self.cleaned_data.get("email", "")
        if commit:
            usuario.save()
            perfil.save()
        return perfil
