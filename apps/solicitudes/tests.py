"""
Pruebas automatizadas del módulo de solicitudes.

Cubre:
1. Reglas de modelo y permisos de transición (puede_cancelar, puede_gestionar).
2. Validaciones en formularios (fechas congruentes, justificación obligatoria en rechazo).
3. Aislamiento de datos en vistas (un empleado jamás ve solicitudes ajenas).
4. Flujo de aprobación, rechazo y pista de auditoría.
"""

from datetime import date, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from apps.cuentas.models import Area
from apps.solicitudes.models import Solicitud, HistorialSolicitud, TipoSolicitud, EstadoSolicitud
from apps.solicitudes.forms import FormularioCrearSolicitud, FormularioAccionSolicitud


class ModelosSolicitudTest(TestCase):
    """Pruebas unitarias para modelos y reglas de negocio."""

    def setUp(self):
        self.grupo_jefe = Group.objects.create(name="Jefe de Área")
        self.grupo_emp = Group.objects.create(name="Empleado")

        self.area_ventas = Area.objects.create(nombre="Ventas")
        self.area_ti = Area.objects.create(nombre="Tecnologías de Información")

        # Empleado de Ventas
        self.emp = User.objects.create_user(username="emp_ventas", password="pw")
        self.emp.groups.add(self.grupo_emp)
        self.emp.perfil.area = self.area_ventas
        self.emp.perfil.save()

        # Jefe de Ventas
        self.jefe_ventas = User.objects.create_user(username="jefe_ventas", password="pw")
        self.jefe_ventas.groups.add(self.grupo_jefe)
        self.jefe_ventas.perfil.area = self.area_ventas
        self.jefe_ventas.perfil.save()
        self.area_ventas.jefe = self.jefe_ventas
        self.area_ventas.save()

        # Empleado de TI (otra área)
        self.emp_ti = User.objects.create_user(username="emp_ti", password="pw")
        self.emp_ti.groups.add(self.grupo_emp)
        self.emp_ti.perfil.area = self.area_ti
        self.emp_ti.perfil.save()

        # Solicitud inicial
        self.solicitud = Solicitud.objects.create(
            solicitante=self.emp,
            area=self.area_ventas,
            tipo=TipoSolicitud.VACACIONES,
            estado=EstadoSolicitud.PENDIENTE,
            asunto="Vacaciones de Verano",
            descripcion="Días correspondientes al primer periodo.",
            fecha_inicio=date.today() + timedelta(days=5),
            fecha_fin=date.today() + timedelta(days=15),
        )

    def test_reglas_puede_cancelar(self):
        """Solo el solicitante original puede cancelar mientras esté pendiente."""
        self.assertTrue(self.solicitud.puede_cancelar(self.emp))
        self.assertFalse(self.solicitud.puede_cancelar(self.emp_ti))
        self.assertFalse(self.solicitud.puede_cancelar(self.jefe_ventas))

        # Si ya fue aprobada, el creador ya no puede cancelarla directamente
        self.solicitud.estado = EstadoSolicitud.APROBADA
        self.solicitud.save()
        self.assertFalse(self.solicitud.puede_cancelar(self.emp))

    def test_reglas_puede_gestionar(self):
        """Solo el jefe del área de la solicitud (o admin) puede resolverla."""
        self.assertTrue(self.solicitud.puede_gestionar(self.jefe_ventas))
        self.assertFalse(self.solicitud.puede_gestionar(self.emp))
        self.assertFalse(self.solicitud.puede_gestionar(self.emp_ti))


class FormulariosSolicitudTest(TestCase):
    """Validación cruzada de datos en los formularios."""

    def test_fechas_incongruentes_invalida_formulario(self):
        """Fecha de término previa a la fecha de inicio debe arrojar error."""
        data = {
            "tipo": TipoSolicitud.VACACIONES,
            "asunto": "Vacaciones erróneas",
            "descripcion": "Detalle",
            "fecha_inicio": date(2026, 7, 20),
            "fecha_fin": date(2026, 7, 10),  # Anterior a inicio
        }
        form = FormularioCrearSolicitud(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_fin", form.errors)

    def test_rechazo_sin_comentario_invalido(self):
        """Rechazar una solicitud sin justificación viola la política."""
        form = FormularioAccionSolicitud(data={"accion": EstadoSolicitud.RECHAZADA, "comentario": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("comentario", form.errors)

    def test_aprobacion_sin_comentario_es_valida(self):
        """Aprobar no exige comentario obligatorio."""
        form = FormularioAccionSolicitud(data={"accion": EstadoSolicitud.APROBADA, "comentario": ""})
        self.assertTrue(form.is_valid())


class FlujoSeguridadSolicitudesTest(TestCase):
    """Pruebas de integración para verificar permisos en vistas y aislamiento de datos."""

    def setUp(self):
        self.client = Client()

        self.grupo_jefe = Group.objects.create(name="Jefe de Área")
        self.grupo_emp = Group.objects.create(name="Empleado")

        self.area_ventas = Area.objects.create(nombre="Ventas")
        self.area_taller = Area.objects.create(nombre="Taller")

        # Empleado 1 (Ventas)
        self.emp1 = User.objects.create_user(username="emp1", password="pw1")
        self.emp1.groups.add(self.grupo_emp)
        self.emp1.perfil.area = self.area_ventas
        self.emp1.perfil.save()

        # Empleado 2 (Taller)
        self.emp2 = User.objects.create_user(username="emp2", password="pw2")
        self.emp2.groups.add(self.grupo_emp)
        self.emp2.perfil.area = self.area_taller
        self.emp2.perfil.save()

        # Jefe de Ventas
        self.jefe_ventas = User.objects.create_user(username="jefe_v", password="pwj")
        self.jefe_ventas.groups.add(self.grupo_jefe)
        self.jefe_ventas.perfil.area = self.area_ventas
        self.jefe_ventas.perfil.save()
        self.area_ventas.jefe = self.jefe_ventas
        self.area_ventas.save()

        # Solicitud de emp1
        self.solicitud = Solicitud.objects.create(
            solicitante=self.emp1,
            area=self.area_ventas,
            tipo=TipoSolicitud.PERMISO,
            asunto="Cita médica",
            descripcion="Permiso de 2 horas",
        )

    def test_empleado_solo_ve_sus_propias_solicitudes(self):
        """El listado de solicitudes para un empleado no contiene registros de otros."""
        self.client.login(username="emp2", password="pw2")
        response = self.client.get(reverse("solicitudes:lista"))
        self.assertEqual(response.status_code, 200)
        # La solicitud de emp1 no debe estar presente en el contexto de emp2
        self.assertNotIn(self.solicitud, response.context["solicitudes"])

    def test_empleado_ajeno_recibe_403_al_consultar_detalle(self):
        """Si un empleado intenta acceder por ID a la solicitud de otro, recibe 403 Forbidden."""
        self.client.login(username="emp2", password="pw2")
        response = self.client.get(reverse("solicitudes:detalle", kwargs={"pk": self.solicitud.pk}))
        self.assertEqual(response.status_code, 403)

    def test_jefe_de_area_puede_ver_y_aprobar(self):
        """El jefe de área correspondiente puede ver el detalle y aprobar la solicitud."""
        self.client.login(username="jefe_v", password="pwj")
        # 1. Consulta el detalle con éxito
        response = self.client.get(reverse("solicitudes:detalle", kwargs={"pk": self.solicitud.pk}))
        self.assertEqual(response.status_code, 200)

        # 2. Aprueba la solicitud
        post_response = self.client.post(
            reverse("solicitudes:gestionar", kwargs={"pk": self.solicitud.pk}),
            {"accion": EstadoSolicitud.APROBADA, "comentario": "Aprobado sin inconvenientes"},
        )
        self.assertEqual(post_response.status_code, 302)

        # 3. Verifica el cambio de estado y la auditoría
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, EstadoSolicitud.APROBADA)
        historial = self.solicitud.historial.last()
        self.assertEqual(historial.estado_nuevo, EstadoSolicitud.APROBADA)
        self.assertEqual(historial.usuario, self.jefe_ventas)
        self.assertIn("Aprobado", historial.comentario)
