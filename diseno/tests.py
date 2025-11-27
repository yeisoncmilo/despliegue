from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Diseno, ArchivoDiseno
from .forms import DisenoForm, ArchivoDisenoInlineFormSet
from produccion.models import OrdenProduccion

User = get_user_model()


class DisenoModelTest(TestCase):
    def setUp(self):
        self.orden = OrdenProduccion.objects.create(numero="ORD-0001")

    def test_diseno_con_orden_str(self):
        diseno = Diseno.objects.create(
            numero="D-0001",
            nombre="Diseño de prueba",
            tipo="orden",
            orden=self.orden
        )
        self.assertEqual(str(diseno), "Diseño #D-0001 - Orden #ORD-0001")

    def test_diseno_sin_orden_str(self):
        diseno = Diseno.objects.create(
            numero="D-0002",
            nombre="Diseño libre",
            tipo="libre"
        )
        self.assertEqual(str(diseno), "Diseño #D-0002 - Diseño libre (Libre)")


class ArchivoDisenoModelTest(TestCase):
    def setUp(self):
        self.diseno = Diseno.objects.create(numero="D-0003", nombre="Test")

    def test_nombre_archivo_automatico(self):
        archivo = SimpleUploadedFile("test.pdf", b"contenido fake")
        archivo_diseno = ArchivoDiseno.objects.create(diseno=self.diseno, archivo=archivo)
        self.assertEqual(archivo_diseno.nombre, "test.pdf")


class DisenoFormTest(TestCase):
    def test_form_valid(self):
        form_data = {
            "numero": "D-0004",
            "nombre": "Diseño Form",
            "descripcion": "Descripción",
            "tipo": "libre",
            "orden": ""
        }
        form = DisenoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_sin_numero(self):
        form_data = {
            "nombre": "Sin número",
            "tipo": "libre"
        }
        form = DisenoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("numero", form.errors)


class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")
        self.orden = OrdenProduccion.objects.create(numero="ORD-0002")

    def test_lista_disenos(self):
        Diseno.objects.create(numero="D-0005", nombre="Test Lista", tipo="libre")
        response = self.client.get("/diseno/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "D-0005")

    def test_crear_diseno_libre(self):
        archivo = SimpleUploadedFile("test.pdf", b"contenido fake")
        response = self.client.post("/diseno/nuevo/", {
            "numero": "D-0006",
            "nombre": "Diseño Libre",
            "tipo": "libre",
            "archivos-TOTAL_FORMS": "1",
            "archivos-INITIAL_FORMS": "0",
            "archivos-0-archivo": archivo,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Diseno.objects.filter(numero="D-0006").exists())

    def test_crear_diseno_con_orden(self):
        archivo = SimpleUploadedFile("test.dwg", b"contenido fake")
        response = self.client.post(f"/diseno/nuevo/{self.orden.pk}/", {
            "numero": "D-0007",
            "nombre": "Diseño Orden",
            "tipo": "orden",
            "orden": self.orden.pk,
            "archivos-TOTAL_FORMS": "1",
            "archivos-INITIAL_FORMS": "0",
            "archivos-0-archivo": archivo,
        })
        self.assertEqual(response.status_code, 302)
        diseno = Diseno.objects.get(numero="D-0007")
        self.assertEqual(diseno.orden, self.orden)

    def test_editar_diseno(self):
        diseno = Diseno.objects.create(numero="D-0008", nombre="Original", tipo="libre")
        response = self.client.post(f"/diseno/{diseno.pk}/editar/", {
            "numero": "D-0008",
            "nombre": "Editado",
            "tipo": "libre",
            "archivos-TOTAL_FORMS": "0",
            "archivos-INITIAL_FORMS": "0",
        })
        self.assertEqual(response.status_code, 302)
        diseno.refresh_from_db()
        self.assertEqual(diseno.nombre, "Editado")

    def test_eliminar_diseno(self):
        diseno = Diseno.objects.create(numero="D-0009", nombre="AEliminar", tipo="libre")
        response = self.client.post(f"/diseno/{diseno.pk}/eliminar/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Diseno.objects.filter(numero="D-0009").exists())