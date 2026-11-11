"""
Configuración de la app 'cuentas'.

AppConfig es la manera en que Django identifica cada app y sus metadatos.
El atributo 'name' debe coincidir exactamente con la ruta de importación.
"""
from django.apps import AppConfig


class CuentasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cuentas"
    verbose_name = "Cuentas y Acceso"  # Nombre que aparece en el panel de administración
