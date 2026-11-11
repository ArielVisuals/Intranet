"""
Decoradores de rol para proteger vistas por grupo de usuario.

En Django, un decorador es una función que "envuelve" a otra función
para agregar comportamiento extra antes o después. Es el mismo concepto
de Higher-Order Components (HOC) en React, o middlewares en Express.js.

Uso:
    @login_required              → solo usuarios con sesión
    @requiere_rol('Empleado')    → solo empleados
    @requiere_rol('Jefe de Área', 'Administrador')  → jefes O administradores
"""

from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.conf import settings


def requiere_rol(*roles_permitidos):
    """
    Decorador factory: recibe los roles permitidos y devuelve el decorador real.
    Si el usuario no tiene ninguno de los roles, lanza PermissionDenied (HTTP 403).

    Ejemplo:
        @requiere_rol('Jefe de Área', 'Administrador')
        def aprobar_solicitud(request, pk):
            ...
    """
    def decorador(view_func):
        @wraps(view_func)  # Preserva el nombre y docstring de la vista original
        def _vista_protegida(request, *args, **kwargs):
            # Primero verificamos que haya sesión activa
            if not request.user.is_authenticated:
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")

            # Los superusuarios (admin creado con createsuperuser) siempre pasan
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Verificamos si el usuario pertenece a alguno de los roles permitidos.
            # filter(name__in=roles_permitidos) es una consulta SQL: WHERE name IN (...)
            tiene_rol = request.user.groups.filter(name__in=roles_permitidos).exists()
            if not tiene_rol:
                raise PermissionDenied  # Django muestra la página 403

            return view_func(request, *args, **kwargs)
        return _vista_protegida
    return decorador


def requiere_jefe_o_admin(view_func):
    """
    Atajo: protege vistas para Jefe de Área o Administrador.
    Uso directo como decorador sin paréntesis:

        @requiere_jefe_o_admin
        def lista_solicitudes_area(request):
            ...
    """
    return requiere_rol("Jefe de Área", "Administrador")(view_func)


def requiere_admin(view_func):
    """Atajo: solo Administradores (o superusuarios)."""
    return requiere_rol("Administrador")(view_func)


# =============================================================================
# FUNCIONES UTILITARIAS DE ROL
# =============================================================================
# Estas funciones se usan dentro de las vistas para verificar el rol
# del usuario SIN redirigir, solo retornando True/False.

def es_empleado(user):
    """True si el usuario pertenece al grupo Empleado."""
    return user.groups.filter(name="Empleado").exists()


def es_jefe(user):
    """True si el usuario pertenece al grupo Jefe de Área."""
    return user.groups.filter(name="Jefe de Área").exists()


def es_administrador(user):
    """True si el usuario es superusuario o del grupo Administrador."""
    return user.is_superuser or user.groups.filter(name="Administrador").exists()
