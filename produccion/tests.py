from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from .models import OrdenProduccion, MaterialProduccion
from .forms import OrdenProduccionForm, MaterialProduccionForm
from cotizaciones.models import Cotizacion

User = get_user_model()


class OrdenProduccionModelTest(TestCase):
    def test_numero_autogenerado(self):
        orden = OrdenProduccion.objects.create(
            cliente_nombre="Cliente Test",
            telefono="3001234567",
            correo_electronico="test@example.com",
            tipo_tablero="MDF",
            dimensiones="2440x1220x18mm",
            color="Blanco"
        )
        self.assertTrue(orden.numero.startswith("ORD-"))

    def test_str_method(self):
        orden = OrdenProduccion.objects.create(
            cliente_nombre="Juan Pérez",
            telefono="3001234567",
            correo_electronico="juan@example.com",
            tipo_tablero="Melamina",
            dimensiones="2440x1220x18mm",
            color="Negro"
        )
        self.assertEqual(str(orden), f"Orden #{orden.numero} - Juan Pérez")

    def test_total_materiales(self):
        orden = OrdenProduccion.objects.create(
            cliente_nombre="Cliente Material",
            telefono="3001234567",
            correo_electronico="mat@example.com",
            tipo_tablero="Plywood",
            dimensiones="2440x1220x18mm",
            color="Natural"
        )
        MaterialProduccion.objects.create(orden=orden, nombre="Tornillos", cantidad=50)
        MaterialProduccion.objects.create(orden=orden, nombre="Lijas", cantidad=10)
        self.assertEqual(orden.total_materiales, 2)


class MaterialProduccionModelTest(TestCase):
    def setUp(self):
        self.orden = OrdenProduccion.objects.create(
            cliente_nombre="Cliente Material",
            telefono="3001234567",
            correo_electronico="mat@example.com",
            tipo_tablero="Plywood",
            dimensiones="2440x1220x18mm",
            color="Natural"
        )

    def test_str_method(self):
        material = MaterialProduccion.objects.create(orden=self.orden, nombre="Clavos", cantidad=100)
        self.assertEqual(str(material), "Clavos - 100 unidades")


class FormsTest(TestCase):
    def test_orden_form_valid(self):
        form_data = {
            "cliente_nombre": "Cliente Form",
            "telefono": "3001234567",
            "correo_electronico": "form@example.com",
            "tipo_tablero": "MDF",
            "dimensiones": "2440x1220x18mm",
            "color": "Blanco",
            "estado": "pendiente"
        }
        form = OrdenProduccionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_material_form_invalid_cantidad_cero(self):
        form_data = {
            "nombre": "Tornillos",
            "cantidad": 0
        }
        form = MaterialProduccionForm(data=form_data)
        self.assertFalse(form.is_valid())


class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")
        self.cotizacion = Cotizacion.objects.create(
            cliente_nombre="Cliente Cotizacion",
            correo_electronico="cot@example.com",
            telefono="3001112222"
        )

    def test_lista_ordenes(self):
        OrdenProduccion.objects.create(
            cliente_nombre="Cliente Lista",
            telefono="3001234567",
            correo_electronico="lista@example.com",
            tipo_tablero="MDF",
            dimensiones="2440x1220x18mm",
            color="Blanco"
        )
        response = self.client.get("/produccion/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cliente Lista")

    def test_crear_orden_con_archivo(self):
        archivo = SimpleUploadedFile("plano.pdf", b"contenido fake")
        response = self.client.post("/produccion/crear/", {
            "cliente_nombre": "Cliente Archivo",
            "telefono": "3001234567",
            "correo_electronico": "arch@example.com",
            "tipo_tablero": "MDF",
            "dimensiones": "2440x1220x18mm",
            "color": "Negro",
            "estado": "pendiente",
            "archivo": archivo,
            "material_0_nombre": "Tornillos",
            "material_0_cantidad": 50,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(OrdenProduccion.objects.filter(cliente_nombre="Cliente Archivo").exists())

    def test_editar_orden(self):
        orden = OrdenProduccion.objects.create(
            cliente_nombre="Cliente Original",
            telefono="3001234567",
            correo_electronico="orig@example.com",
            tipo_tablero="MDF",
            dimensiones="2440x1220x18mm",
            color="Blanco"
        )
        response = self.client.post(f"/produccion/{orden.pk}/editar/", {
            "cliente_nombre": "Cliente Editado",
            "telefono": "3001234567",
            "correo_electronico": "edit@example.com",
            "tipo_tablero": "Melamina",
            "dimensiones": "2440x1220x18mm",
            "color": "Negro",
            "estado": "en_proceso",
            "material_0_nombre": "Lijas",
            "material_0_cantidad": 20,
        })
        self.assertEqual(response.status_code, 302)
        orden.refresh_from_db()
        self.assertEqual(orden.cliente_nombre, "Cliente Editado")

    def test_eliminar_orden(self):
        orden = OrdenProduccion.objects.create(
            cliente_nombre="Cliente Eliminar",
            telefono="3001234567",
            correo_electronico="del@example.com",
            tipo_tablero="MDF",
            dimensiones="2440x1220x18mm",
            color="Blanco"
        )
        response = self.client.post(f"/produccion/{orden.pk}/eliminar/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(OrdenProduccion.objects.filter(cliente_nombre="Cliente Eliminar").exists())

    def test_generar_pdf(self):
        orden = OrdenProduccion.objects.create(
            cliente_nombre="Cliente PDF",
            telefono="3001234567",
            correo_electronico="pdf@example.com",
            tipo_tablero="MDF",
            dimensiones="2440x1220x18mm",
            color="Blanco"
        )
        response = self.client.get(f"/produccion/{orden.pk}/pdf/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    @patch("django.core.mail.EmailMessage.send")
    def test_enviar_correo(self, mock_send):
        orden = OrdenProduccion.objects.create(
            cliente_nombre="Cliente Correo",
            telefono="3001234567",
            correo_electronico="correo@example.com",
            tipo_tablero="MDF",
            dimensiones="2440x1220x18mm",
            color="Blanco"
        )
        response = self.client.post(f"/produccion/{orden.pk}/enviar-correo/")
        self.assertEqual(response.status_code, 302)
        mock_send.assert_called_once()

    def test_ajax_cargar_cotizacion(self):
        response = self.client.get(f"/produccion/ajax/cargar-cotizacion/{self.cotizacion.pk}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["cliente_nombre"], "Cliente Cotizacion")
        self.assertEqual(data["correo_electronico"], "cot@example.com")