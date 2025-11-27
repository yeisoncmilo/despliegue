from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from .models import Venta, VentaTablero, VentaMaterial
from .forms import VentaForm
from cotizaciones.models import Cotizacion, Tablero, Material

User = get_user_model()


class VentaModelTest(TestCase):
    def test_numero_autogenerado(self):
        venta = Venta.objects.create(
            cliente_nombre="Cliente Test",
            telefono="3001234567",
            correo_electronico="test@example.com"
        )
        self.assertTrue(venta.numero.startswith("VNT-"))

    def test_str_method(self):
        venta = Venta.objects.create(
            cliente_nombre="Juan Pérez",
            telefono="3001234567",
            correo_electronico="juan@example.com"
        )
        self.assertEqual(str(venta), f"Venta #{venta.numero} - Juan Pérez")

    def test_total_sin_tableros(self):
        venta = Venta.objects.create(
            cliente_nombre="Cliente Sin Items",
            telefono="3001234567",
            correo_electronico="sin@example.com"
        )
        self.assertEqual(venta.subtotal, 0)
        self.assertEqual(venta.total, 0)


class VentaTableroModelTest(TestCase):
    def setUp(self):
        self.venta = Venta.objects.create(
            cliente_nombre="Cliente Tablero",
            telefono="3001234567",
            correo_electronico="tab@example.com"
        )
        self.tablero = VentaTablero.objects.create(
            venta=self.venta,
            descripcion="Tablero principal",
            valor_tablero=1000000,
            descuento_tablero=10,
            orden=0
        )

    def test_subtotal_tablero_bruto(self):
        self.assertEqual(self.tablero.subtotal_tablero_bruto, 900000)

    def test_subtotal_sin_materiales(self):
        self.assertEqual(self.tablero.subtotal_tablero, 900000)


class VentaMaterialModelTest(TestCase):
    def setUp(self):
        self.venta = Venta.objects.create(
            cliente_nombre="Cliente Material",
            telefono="3001234567",
            correo_electronico="mat@example.com"
        )
        self.tablero = VentaTablero.objects.create(
            venta=self.venta,
            descripcion="Tablero con materiales",
            valor_tablero=500000,
            descuento_tablero=0,
            orden=0
        )
        self.material = VentaMaterial.objects.create(
            venta_tablero=self.tablero,
            nombre="Cable 2.5mm",
            cantidad=10,
            valor_unitario=5000,
            descuento=5
        )

    def test_subtotal_material(self):
        self.assertEqual(self.material.subtotal, 47500)


class VentaFormTest(TestCase):
    def test_form_valid(self):
        form_data = {
            "cliente_nombre": "Cliente Form",
            "telefono": "3001234567",
            "correo_electronico": "form@example.com",
            "estado": "pendiente",
            "metodo_pago": "transferencia"
        }
        form = VentaForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_email(self):
        form_data = {
            "cliente_nombre": "Cliente Form",
            "telefono": "3001234567",
            "correo_electronico": "correo-invalido",
            "estado": "pendiente",
            "metodo_pago": "efectivo"
        }
        form = VentaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("correo_electronico", form.errors)


class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")
        self.cotizacion = Cotizacion.objects.create(
            cliente_nombre="Cliente Cotizacion",
            correo_electronico="cot@example.com",
            telefono="3001112222",
            estado="aprobada"
        )
        self.tablero = Tablero.objects.create(
            cotizacion=self.cotizacion,
            descripcion="Tablero de prueba",
            valor_tablero=100000,
            descuento_tablero=0,
            orden=0
        )
        Material.objects.create(
            tablero=self.tablero,
            nombre="Tornillo",
            cantidad=10,
            valor_unitario=1000,
            descuento=0
        )

    def test_lista_ventas(self):
        Venta.objects.create(
            cliente_nombre="Cliente Lista",
            telefono="3001234567",
            correo_electronico="lista@example.com"
        )
        response = self.client.get("/ventas/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cliente Lista")

    def test_crear_venta_desde_cotizacion(self):
        response = self.client.post(f"/ventas/crear/{self.cotizacion.pk}/", {
            "cliente_nombre": "Cliente Venta",
            "telefono": "3001234567",
            "correo_electronico": "venta@example.com",
            "estado": "pendiente",
            "metodo_pago": "transferencia",
            "tablero_0_descripcion": "Tablero de prueba",
            "tablero_0_valor_tablero": 100000,
            "tablero_0_descuento_tablero": 0,
            "tablero_0_descuento_materiales": 0,
            "tablero_0_material_0_nombre": "Tornillo",
            "tablero_0_material_0_cantidad": 10,
            "tablero_0_material_0_valor_unitario": 1000,
            "tablero_0_material_0_descuento": 0,
        })
        self.assertEqual(response.status_code, 302)
        venta = Venta.objects.get(cliente_nombre="Cliente Venta")
        self.assertEqual(venta.cotizacion, self.cotizacion)

    def test_editar_venta(self):
        venta = Venta.objects.create(
            cliente_nombre="Cliente Original",
            telefono="3001234567",
            correo_electronico="orig@example.com"
        )
        response = self.client.post(f"/ventas/{venta.pk}/editar/", {
            "cliente_nombre": "Cliente Editado",
            "telefono": "3001234567",
            "correo_electronico": "edit@example.com",
            "estado": "pagada",
            "metodo_pago": "tarjeta"
        })
        self.assertEqual(response.status_code, 302)
        venta.refresh_from_db()
        self.assertEqual(venta.cliente_nombre, "Cliente Editado")

    def test_eliminar_venta(self):
        venta = Venta.objects.create(
            cliente_nombre="Cliente Eliminar",
            telefono="3001234567",
            correo_electronico="del@example.com"
        )
        response = self.client.post(f"/ventas/{venta.pk}/eliminar/")
        self.assertEqual(response.status_code, 302)
        venta.refresh_from_db()
        self.assertEqual(venta.estado, "anulada")

    def test_generar_pdf(self):
        venta = Venta.objects.create(
            cliente_nombre="Cliente PDF",
            telefono="3001234567",
            correo_electronico="pdf@example.com"
        )
        response = self.client.get(f"/ventas/{venta.pk}/pdf/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    @patch("django.core.mail.EmailMessage.send")
    def test_enviar_correo(self, mock_send):
        venta = Venta.objects.create(
            cliente_nombre="Cliente Correo",
            telefono="3001234567",
            correo_electronico="correo@example.com"
        )
        VentaTablero.objects.create(
            venta=venta,
            descripcion="Item de prueba",
            valor_tablero=100000,
            descuento_tablero=0,
            orden=0
        )
        response = self.client.post(f"/ventas/{venta.pk}/enviar-correo/")
        self.assertEqual(response.status_code, 302)
        mock_send.assert_called_once()

    def test_ajax_cargar_cotizacion(self):
        response = self.client.get(f"/ventas/ajax/cargar-cotizacion/{self.cotizacion.pk}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["cliente_nombre"], "Cliente Cotizacion")
        self.assertEqual(len(data["tableros"]), 1)

    def test_convertir_cotizacion_a_venta(self):
        response = self.client.get(f"/ventas/convertir-cotizacion/{self.cotizacion.pk}/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"/ventas/crear/{self.cotizacion.pk}/")