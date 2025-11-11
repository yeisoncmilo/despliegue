from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Cotizacion(models.Model):
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("aprobada", "Aprobada"),
        ("rechazada", "Rechazada"),
    ]
    numero = models.CharField(max_length=50, unique=True, editable=False)
    cliente_nombre = models.CharField(max_length=200)
    razon_social = models.CharField(max_length=200, blank=True)
    nit = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=300, blank=True)
    telefono = models.CharField(max_length=20)
    correo_electronico = models.EmailField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="pendiente")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"Cotización #{self.numero} - {self.cliente_nombre}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generar_numero()
        super().save(*args, **kwargs)

    @staticmethod
    def generar_numero():
        """Genera el siguiente número de cotización automáticamente"""
        ultima = Cotizacion.objects.all().order_by('-id').first()
        if ultima and ultima.numero.startswith('COT-'):
            try:
                ultimo_numero = int(ultima.numero.split('-')[1])
                nuevo_numero = ultimo_numero + 1
            except (IndexError, ValueError):
                nuevo_numero = 1
        else:
            nuevo_numero = 1
        return f"COT-{nuevo_numero:04d}"

    @property
    def subtotal(self):
        return sum(t.subtotal_tablero for t in self.tableros.all())

    @property
    def iva(self):
        return int(self.subtotal * 19 / 100)

    @property
    def total(self):
        return self.subtotal + self.iva


class Tablero(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name="tableros")
    descripcion = models.TextField(blank=True, null=True)
    valor_tablero = models.PositiveIntegerField(default=0)
    descuento_tablero = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    descuento_materiales = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"Tablero #{self.orden + 1} - {self.cotizacion.numero}"

    @property
    def subtotal_tablero_bruto(self):
        return int(self.valor_tablero * (100 - self.descuento_tablero) / 100)

    @property
    def subtotal_materiales(self):
        total = sum(m.subtotal for m in self.materiales.all())
        return int(total * (100 - self.descuento_materiales) / 100)

    @property
    def subtotal_tablero(self):
        return self.subtotal_tablero_bruto + self.subtotal_materiales


class Material(models.Model):
    tablero = models.ForeignKey(Tablero, on_delete=models.CASCADE, related_name="materiales")
    nombre = models.CharField(max_length=200)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    valor_unitario = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(99999999)])
    descuento = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    def __str__(self):
        return f"{self.nombre} - {self.cantidad} unidades"

    @property
    def subtotal(self):
        total = self.cantidad * self.valor_unitario
        return int(total * (100 - self.descuento) / 100)