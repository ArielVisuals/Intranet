"""
Pruebas automatizadas para la app 'cuentas'.

En Django, los tests heredan de TestCase (proporcionado por django.test).
Cada prueba se ejecuta dentro de una transacción de base de datos aislada
que se revierte al terminar, por lo que una prueba nunca ensucia los datos
de otra (es el equivalente a mockear o hacer rollback en un runner como Jest).

Probamos:
1. Creación automática de PerfilUsuario mediante la señal post_save.
2. Asociación de usuario con Área y roles (Groups).
3. Vistas de Login y Logout (autenticación y redirecciones).
4. Vista de Perfil (acceso protegido y actualización de datos).
5. Decoradores de permisos por rol (@requiere_rol).
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from apps.cuentas.models import Area, PerfilUsuario
from apps.cuentas.decorators import (
    requiere_rol,
    es_empleado,
    es_jefe,
    es_administrador,
)


class ModelosCuentasTest(TestCase):
    """Pruebas unitarias para los modelos Area, PerfilUsuario y sus señales."""

    def setUp(self):
        """
        setUp se ejecuta antes de cada test.
        Equivale al beforeEach() en Jest o Mocha de JavaScript.
        """
        self.area = Area.objects.create(
            nombre="Ventas",
            descripcion="Área encargada de comercialización y atención al cliente",
        )
        self.user = User.objects.create_user(
            username="empleado1",
            password="PasswordSeguro123!",
            first_name="Carlos",
            last_name="Ramírez",
            email="carlos@lexusuniversidad.com",
        )

    def test_creacion_automatica_de_perfil_por_signal(self):
        """Verifica que la señal post_save cree un PerfilUsuario al guardar un User."""
        self.assertTrue(hasattr(self.user, "perfil"))
        self.assertIsInstance(self.user.perfil, PerfilUsuario)

    def test_asignar_area_a_perfil(self):
        """Verifica que se pueda asociar un área al perfil del usuario."""
        perfil = self.user.perfil
        perfil.area = self.area
        perfil.puesto = "Ejecutivo de Ventas"
        perfil.telefono = "5512345678"
        perfil.save()

        self.assertEqual(self.user.perfil.area.nombre, "Ventas")
        self.assertEqual(self.area.empleados.count(), 1)

    def test_roles_y_metodos_de_perfil(self):
        """Verifica la asignación de grupos (roles) y los métodos utilitarios."""
        grupo_empleado, _ = Group.objects.get_or_create(name="Empleado")
        self.user.groups.add(grupo_empleado)

        self.assertTrue(es_empleado(self.user))
        self.assertFalse(es_jefe(self.user))
        self.assertFalse(es_administrador(self.user))
        self.assertEqual(self.user.perfil.get_rol_display(), "Empleado")


class VistasAutenticacionTest(TestCase):
    """Pruebas de integración para las vistas de login, logout y perfil."""

    def setUp(self):
        self.client = Client()  # Cliente HTTP simulado de Django (como Supertest en Node)
        self.user = User.objects.create_user(
            username="ana_lopez",
            password="Password123!",
            first_name="Ana",
            last_name="López",
            email="ana@lexusuniversidad.com",
        )

    def test_pagina_login_accesible(self):
        """La página de login debe responder con código HTTP 200 y usar la plantilla correcta."""
        response = self.client.get(reverse("cuentas:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cuentas/login.html")
        self.assertContains(response, "Portal Universidad")

    def test_login_exitoso_redirecciona(self):
        """Un login con credenciales válidas debe autenticar y redirigir al dashboard."""
        response = self.client.post(reverse("cuentas:login"), {
            "username": "ana_lopez",
            "password": "Password123!",
        })
        # Redirige a /portal/dashboard/ (código 302 en HTTP)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("portal:dashboard"))

    def test_login_invalido_muestra_error(self):
        """Credenciales incorrectas deben recargar la página y mostrar error."""
        response = self.client.post(reverse("cuentas:login"), {
            "username": "ana_lopez",
            "password": "PasswordIncorrecto",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)

    def test_perfil_requiere_autenticacion(self):
        """Un usuario anónimo que entra a /cuentas/perfil/ debe ser redirigido a login."""
        response = self.client.get(reverse("cuentas:perfil"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("cuentas:login"), response.url)

    def test_actualizar_perfil_usuario_autenticado(self):
        """Un usuario con sesión puede actualizar sus datos desde su perfil."""
        self.client.login(username="ana_lopez", password="Password123!")
        response = self.client.post(reverse("cuentas:perfil"), {
            "nombre": "Ana María",
            "apellido": "López Vega",
            "email": "anamaria@lexusuniversidad.com",
            "puesto": "Coordinadora",
            "telefono": "5598765432",
            "fecha_ingreso": "2024-01-15",
        })
        # Debe redirigir de vuelta al perfil tras guardar
        self.assertEqual(response.status_code, 302)

        # Recargamos el usuario desde la base de datos para verificar cambios
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Ana María")
        self.assertEqual(self.user.perfil.puesto, "Coordinadora")
        self.assertEqual(self.user.perfil.telefono, "5598765432")


class DecoradoresPermisosTest(TestCase):
    """Pruebas para el decorador @requiere_rol y el control de accesos."""

    def setUp(self):
        self.factory = RequestFactory()  # Permite simular una petición HTTP directa
        self.grupo_jefe = Group.objects.create(name="Jefe de Área")
        self.grupo_empleado = Group.objects.create(name="Empleado")

        self.user_jefe = User.objects.create_user(username="jefe1", password="pw")
        self.user_jefe.groups.add(self.grupo_jefe)

        self.user_empleado = User.objects.create_user(username="emp1", password="pw")
        self.user_empleado.groups.add(self.grupo_empleado)

    def test_requiere_rol_permite_acceso_a_rol_valido(self):
        """Un usuario con el rol requerido puede ejecutar la vista protegida."""
        @requiere_rol("Jefe de Área")
        def vista_demo(request):
            return "OK"

        request = self.factory.get("/ruta-protegida/")
        request.user = self.user_jefe
        resultado = vista_demo(request)
        self.assertEqual(resultado, "OK")

    def test_requiere_rol_deniega_acceso_a_rol_invalido(self):
        """Un usuario sin el rol requerido recibe excepción PermissionDenied (HTTP 403)."""
        @requiere_rol("Jefe de Área")
        def vista_demo(request):
            return "OK"

        request = self.factory.get("/ruta-protegida/")
        request.user = self.user_empleado

        with self.assertRaises(PermissionDenied):
            vista_demo(request)
