"""
Pruebas automatizadas para la app 'documentos'.

Cubre:
1. Reglas del modelo (cálculo de tamaño, iconos por extensión y permisos de acceso).
2. Validación de formularios (bloqueo de extensiones no permitidas y límite de tamaño).
3. Aislamiento de visibilidad en el listado y bloqueo de descargas ajenas (HTTP 403).
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from apps.cuentas.models import Area
from apps.documentos.models import Documento, CategoriaDocumento, VisibilidadDocumento
from apps.documentos.forms import FormularioDocumento


class ModelosDocumentoTest(TestCase):
    """Pruebas unitarias para el modelo Documento y métodos auxiliares."""

    def setUp(self):
        self.area_ventas = Area.objects.create(nombre="Ventas")
        self.area_taller = Area.objects.create(nombre="Taller")

        self.user_ventas = User.objects.create_user(username="u_ventas", password="pw")
        self.user_ventas.perfil.area = self.area_ventas
        self.user_ventas.perfil.save()

        self.user_taller = User.objects.create_user(username="u_taller", password="pw")
        self.user_taller.perfil.area = self.area_taller
        self.user_taller.perfil.save()

        # Archivo simulado en memoria
        archivo_prueba = SimpleUploadedFile("manual_ventas.pdf", b"Contenido binario de prueba", content_type="application/pdf")

        self.doc_area = Documento.objects.create(
            titulo="Manual de Ventas",
            categoria=CategoriaDocumento.MANUALES,
            archivo=archivo_prueba,
            visibilidad=VisibilidadDocumento.SOLO_AREA,
            area=self.area_ventas,
            subido_por=self.user_ventas,
        )

        self.doc_publico = Documento.objects.create(
            titulo="Código de Ética",
            categoria=CategoriaDocumento.POLITICAS,
            archivo=SimpleUploadedFile("codigo.pdf", b"Contenido", content_type="application/pdf"),
            visibilidad=VisibilidadDocumento.TODA_EMPRESA,
            subido_por=self.user_ventas,
        )

    def tearDown(self):
        # Limpieza de archivos creados en el test
        if self.doc_area.archivo:
            self.doc_area.archivo.delete(save=False)
        if self.doc_publico.archivo:
            self.doc_publico.archivo.delete(save=False)

    def test_reglas_visibilidad_puede_acceder(self):
        """El documento de toda la empresa es visible para todos; el de área solo para miembros."""
        # Código de ética (público)
        self.assertTrue(self.doc_publico.puede_acceder(self.user_ventas))
        self.assertTrue(self.doc_publico.puede_acceder(self.user_taller))

        # Manual de ventas (restringido)
        self.assertTrue(self.doc_area.puede_acceder(self.user_ventas))
        self.assertFalse(self.doc_area.puede_acceder(self.user_taller))

    def test_propiedades_extension_icono_y_tamanio(self):
        """Verifica que la extensión y el icono de Bootstrap coincidan con el tipo de archivo."""
        self.assertEqual(self.doc_area.extension, ".pdf")
        self.assertIn("bi-file-earmark-pdf", self.doc_area.icono_bootstrap)
        self.assertTrue(self.doc_area.tamanio_legible.endswith("B"))


class FormularioDocumentoTest(TestCase):
    """Validación de tipo de archivo y tamaño máximo en formularios."""

    def test_archivo_valido_pasa_validacion(self):
        archivo = SimpleUploadedFile("politica.docx", b"x" * 1024, content_type="application/vnd.openxmlformats")
        data = {
            "titulo": "Política de Calidad",
            "categoria": CategoriaDocumento.POLITICAS,
            "visibilidad": VisibilidadDocumento.TODA_EMPRESA,
        }
        form = FormularioDocumento(data=data, files={"archivo": archivo})
        self.assertTrue(form.is_valid())

    def test_archivo_extension_no_permitida_falla(self):
        """Extensiones ejecutables o peligrosas (.exe, .sh) deben ser rechazadas."""
        archivo = SimpleUploadedFile("malware.exe", b"malware", content_type="application/octet-stream")
        data = {
            "titulo": "Archivo no deseado",
            "categoria": CategoriaDocumento.POLITICAS,
            "visibilidad": VisibilidadDocumento.TODA_EMPRESA,
        }
        form = FormularioDocumento(data=data, files={"archivo": archivo})
        self.assertFalse(form.is_valid())
        self.assertIn("archivo", form.errors)

    def test_archivo_excedente_de_tamanio_falla(self):
        """Archivos superiores a 10 MB deben ser rechazados."""
        # 11 Megabytes
        archivo_pesado = SimpleUploadedFile("muy_grande.pdf", b"x" * (11 * 1024 * 1024), content_type="application/pdf")
        data = {
            "titulo": "Archivo pesado",
            "categoria": CategoriaDocumento.POLITICAS,
            "visibilidad": VisibilidadDocumento.TODA_EMPRESA,
        }
        form = FormularioDocumento(data=data, files={"archivo": archivo_pesado})
        self.assertFalse(form.is_valid())
        self.assertIn("archivo", form.errors)


class VistasDocumentosTest(TestCase):
    """Pruebas de aislamiento en consultas y control de descargas en el servidor."""

    def setUp(self):
        self.client = Client()

        self.area_ventas = Area.objects.create(nombre="Ventas")
        self.area_taller = Area.objects.create(nombre="Taller")

        self.user_ventas = User.objects.create_user(username="emp_v", password="pw1")
        self.user_ventas.perfil.area = self.area_ventas
        self.user_ventas.perfil.save()

        self.user_taller = User.objects.create_user(username="emp_t", password="pw2")
        self.user_taller.perfil.area = self.area_taller
        self.user_taller.perfil.save()

        self.doc_ventas = Documento.objects.create(
            titulo="Documento Confidencial Ventas",
            categoria=CategoriaDocumento.FORMATOS,
            archivo=SimpleUploadedFile("ventas_conf.pdf", b"Datos sensibles", content_type="application/pdf"),
            visibilidad=VisibilidadDocumento.SOLO_AREA,
            area=self.area_ventas,
            subido_por=self.user_ventas,
        )

        self.doc_publico = Documento.objects.create(
            titulo="Reglamento Interno de Trabajo",
            categoria=CategoriaDocumento.POLITICAS,
            archivo=SimpleUploadedFile("reglamento.pdf", b"Reglas generales", content_type="application/pdf"),
            visibilidad=VisibilidadDocumento.TODA_EMPRESA,
            subido_por=self.user_ventas,
        )

    def tearDown(self):
        if self.doc_ventas.archivo:
            self.doc_ventas.archivo.delete(save=False)
        if self.doc_publico.archivo:
            self.doc_publico.archivo.delete(save=False)

    def test_listado_oculta_documentos_de_otra_area(self):
        """Un usuario del Taller no debe ver el documento restringido de Ventas."""
        self.client.login(username="emp_t", password="pw2")
        response = self.client.get(reverse("documentos:lista"))
        self.assertEqual(response.status_code, 200)

        # Debe ver el reglamento público
        self.assertIn(self.doc_publico, response.context["documentos"])
        # NO debe ver el documento exclusivo de ventas
        self.assertNotIn(self.doc_ventas, response.context["documentos"])

    def test_descarga_restringida_arroja_403(self):
        """Intentar descargar por URL directa un documento de otra área lanza HTTP 403 Forbidden."""
        self.client.login(username="emp_t", password="pw2")
        response = self.client.get(reverse("documentos:descargar", kwargs={"pk": self.doc_ventas.pk}))
        self.assertEqual(response.status_code, 403)

    def test_descarga_autorizada_entrega_archivo(self):
        """El usuario de Ventas puede descargar su propio documento de área exitosamente."""
        self.client.login(username="emp_v", password="pw1")
        response = self.client.get(reverse("documentos:descargar", kwargs={"pk": self.doc_ventas.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertIn("filename=", response.headers.get("Content-Disposition", ""))
