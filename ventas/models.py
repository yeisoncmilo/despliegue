from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import requests


class Venta(models.Model):
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("pagada",    "Pagada"),
        ("anulada",   "Anulada"),
    ]
    numero          = models.CharField(max_length=50, unique=True)
    fecha           = models.DateTimeField(auto_now_add=True)
    cliente_nombre  = models.CharField(max_length=200)
    razon_social    = models.CharField(max_length=200, blank=True)
    telefono        = models.CharField(max_length=20, blank=True)
    correo          = models.EmailField()
    direccion_envio = models.TextField(blank=True)
    estado          = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="pendiente")
    subtotal        = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva             = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total           = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Campo extra por API
    tipo_cambio_usd = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, editable=False)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Venta #{self.numero} – {self.cliente_nombre}"

    def calcular_totales(self):
        sub = sum(det.subtotal for det in self.detalles.all())
        self.subtotal = sub
        self.iva      = sub * Decimal("0.19")
        self.total    = self.subtotal + self.iva

    def consumir_tipo_cambio(self):
        """API externa: USD->CLP  (mindicador.cl)"""
        try:
            r = requests.get("https://mindicador.cl/api/dolar", timeout=5)
            r.raise_for_status()
            valor = r.json()["serie"][0]["valor"]
            self.tipo_cambio_usd = Decimal(str(valor))
        except Exception:
            # Si falla dejamos None y seguimos
            self.tipo_cambio_usd = None

    def save(self, *args, **kwargs):
        self.calcular_totales()
        # Solo obtenemos tipo de cambio la primera vez
        if self.tipo_cambio_usd is None:
            self.consumir_tipo_cambio()
        super().save(*args, **kwargs)


class DetalleVenta(models.Model):
    venta        = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    descripcion  = models.CharField(max_length=250)
    cantidad     = models.IntegerField(validators=[MinValueValidator(1)])
    precio_unit  = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    descuento    = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    @property
    def subtotal(self):
        total = self.cantidad * self.precio_unit
        return total * (1 - self.descuento / 100)

    def __str__(self):
        return f"{self.descripcion} ({self.cantidad})"