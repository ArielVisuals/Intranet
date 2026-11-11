"""
Configuración de la app 'cuentas'.

La clase AppConfig es el punto de entrada de cada app en Django.
El método ready() se ejecuta una sola vez cuando Django termina de cargar
todas las apps — es el lugar correcto para registrar signals, ya que
garantiza que todos los modelos ya están disponibles.
"""

from django.apps import AppConfig


class CuentasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cuentas"
    verbose_name = "Cuentas y Acceso"

    def ready(self):
        """
        Importar el módulo de modelos activa los decoradores @receiver
        que registran las señales. Sin esta importación, las señales
        (crear perfil al crear usuario) no funcionarían.
        """
        # noqa: F401 silencia la advertencia de "importado pero no usado"
        import apps.cuentas.models  # noqa: F401
