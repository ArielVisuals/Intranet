"""
Modelos de la app 'cuentas': Área y Perfil de Usuario.

En Django, un modelo es una clase Python que se convierte automáticamente
en una tabla SQL. Cada atributo de clase es una columna.
Equivale a definir un schema en SQL, pero con Python puro.

Decisión: extendemos el User de Django con un PerfilUsuario separado
(relación OneToOne) en lugar de reemplazar el modelo User. Esto nos
permite usar todo el sistema de autenticación listo de Django
(login, contraseñas, groups, permisos) sin modificarlo.
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Area(models.Model):
    """
    Área o departamento de la empresa.
    Cada empleado pertenece a un Área, y cada Área tiene un Jefe.

    La ForeignKey a User para el jefe usa null=True porque un área
    puede existir sin jefe asignado (por ejemplo, cuando se crea por primera vez).
    SET_NULL: si se elimina el usuario jefe, el campo jefe queda en NULL
    en lugar de eliminar el área.
    """

    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre del área",
        help_text="Nombre único del área o departamento",
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción breve del área y sus funciones",
    )
    # Un área tiene exactamente un jefe (FK, no OneToOne, porque en teoría
    # el mismo jefe podría dirigir varias áreas si la empresa lo requiere).
    jefe = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="areas_que_dirige",  # user.areas_que_dirige.all() devuelve las áreas que dirige
        verbose_name="Jefe del área",
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        ordering = ["nombre"]  # Django ordenará las consultas por nombre por defecto

    def __str__(self):
        """
        __str__ en Python equivale a toString() en JavaScript.
        Define cómo se muestra el objeto como texto (en el admin, dropdowns, etc.)
        """
        return self.nombre


class PerfilUsuario(models.Model):
    """
    Perfil extendido del usuario. Complementa al User de Django con
    datos específicos del negocio (área, puesto, teléfono).

    OneToOneField: exactamente un perfil por usuario y viceversa.
    Es una ForeignKey con restricción unique=True.
    CASCADE: si se elimina el User, se elimina su perfil automáticamente.
    """

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil",  # user.perfil accede al perfil del usuario
        verbose_name="Usuario",
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="empleados",  # area.empleados.all() devuelve todos en esa área
        verbose_name="Área",
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Teléfono",
    )
    puesto = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Puesto",
    )
    fecha_ingreso = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de ingreso",
    )

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self):
        return f"Perfil de {self.usuario.get_full_name() or self.usuario.username}"

    def get_rol_display(self):
        """
        Devuelve el nombre del rol principal del usuario de forma legible.
        Un usuario puede pertenecer a varios grupos; mostramos el más importante.
        """
        if self.usuario.is_superuser or self.usuario.groups.filter(name="Administrador").exists():
            return "Administrador"
        if self.usuario.groups.filter(name="Jefe de Área").exists():
            return "Jefe de Área"
        return "Empleado"

    def es_jefe(self):
        """Retorna True si el usuario tiene el rol de Jefe de Área."""
        return self.usuario.groups.filter(name="Jefe de Área").exists()

    def es_administrador(self):
        """Retorna True si el usuario es Administrador o superusuario."""
        return self.usuario.is_superuser or self.usuario.groups.filter(name="Administrador").exists()


# =============================================================================
# SEÑALES (SIGNALS)
# =============================================================================
# Una señal es exactamente como un event listener en JavaScript.
# post_save se dispara DESPUÉS de que se guarda un objeto en la base de datos.
# Aquí, cuando Django guarda un nuevo User (created=True), automáticamente
# creamos su PerfilUsuario. El desarrollador no tiene que acordarse de hacerlo.

@receiver(post_save, sender=User)
def crear_perfil_al_crear_usuario(sender, instance, created, **kwargs):
    """
    Se ejecuta automáticamente cuando se crea un nuevo User.
    'created' es True solo la primera vez (INSERT), False en actualizaciones (UPDATE).
    """
    if created:
        PerfilUsuario.objects.get_or_create(usuario=instance)


@receiver(post_save, sender=User)
def guardar_perfil_al_guardar_usuario(sender, instance, **kwargs):
    """
    Garantiza que el perfil se guarda cada vez que se guarda el usuario.
    Usa hasattr para evitar errores si el perfil aún no existe.
    """
    if hasattr(instance, "perfil"):
        instance.perfil.save()
