from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core import mail
from unittest.mock import patch
from .models import Cotizacion, Tablero, Material
from .forms import CotizacionForm

User = get_user_model()


class CotizacionModelTest(TestCase):
    def setUp(self):
        self.cotizacion = Cotizacion.objects.create(
            cliente_nombre="Juan Pérez",
            correo_electronico="juan@example.com",
            telefono="123456789"
        )

    def test_numero_autogenerado(self):
        self.assertTrue(self.cotizacion.numero.startswith("COT-"))

    def test_subtotal_sin_tableros(self):
        self.assertEqual(self.cotizacion.subtotal, 0)

    def test_total_con_iva(self):
        self.assertEqual(self.cotizacion.total, 0)

    def test_str_method(self):
        self.assertEqual(str(self.cotizacion), f"Cotización #{self.cotizacion.numero} - Juan Pérez")


class TableroModelTest(TestCase):
    def setUp(self):
        self.cotizacion = Cotizacion.objects.create(
            cliente_nombre="Empresa ABC",
            correo_electronico="contacto@empresa.com",
            telefono="987654321"
        )
        self.tablero = Tablero.objects.create(
            cotizacion=self.cotizacion,
            descripcion="Tablero principal",
            valor_tablero=1000000,
            descuento_tablero=10,
            orden=0
        )

    def test_subtotal_tablero_bruto(self):
        self.assertEqual(self.tablero.subtotal_tablero_bruto, 900000)

    def test_subtotal_tablero_sin_materiales(self):
        self.assertEqual(self.tablero.subtotal_tablero, 900000)


class MaterialModelTest(TestCase):
    def setUp(self):
        self.cotizacion = Cotizacion.objects.create(
            cliente_nombre="Cliente X",
            correo_electronico="x@example.com",
            telefono="111222333"
        )
        self.tablero = Tablero.objects.create(
            cotizacion=self.cotizacion,
            descripcion="Tablero con materiales",
            valor_tablero=500000,
            descuento_tablero=0,
            orden=0
        )
        self.material = Material.objects.create(
            tablero=self.tablero,
            nombre="Cable 2.5mm",
            cantidad=10,
            valor_unitario=5000,
            descuento=5
        )

    def test_subtotal_material(self):
        self.assertEqual(self.material.subtotal, 47500)


class CotizacionFormTest(TestCase):
    def test_form_valid(self):
        form_data = {
            "cliente_nombre": "Cliente Test",
            "razon_social": "Test S.A.S",
            "nit": "123456-7",
            "direccion": "Calle 123",
            "telefono": "3001234567",
            "correo_electronico": "test@example.com",
            "estado": "pendiente"
        }
        form = CotizacionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_email(self):
        form_data = {
            "cliente_nombre": "Cliente Test",
            "telefono": "3001234567",
            "correo_electronico": "correo-invalido"
        }
        form = CotizacionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("correo_electronico", form.errors)


class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")
        self.cotizacion = Cotizacion.objects.create(
            cliente_nombre="Cliente Vista",
            correo_electronico="vista@example.com",
            telefono="123456789"
        )

    def test_lista_cotizaciones(self):
        response = self.client.get("/cotizaciones/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cliente Vista")

    def test_detalle_cotizacion(self):
        response = self.client.get(f"/cotizaciones/{self.cotizacion.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cotizacion.numero)

    def test_generar_pdf(self):
        response = self.client.get(f"/cotizaciones/pdf/{self.cotizacion.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    @patch("django.core.mail.EmailMessage.send")
    def test_enviar_correo(self, mock_send):
        response = self.client.post(f"/cotizaciones/{self.cotizacion.pk}/enviar-correo/")
        self.assertEqual(response.status_code, 302)
        mock_send.assert_called_once()