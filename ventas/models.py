from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Venta(models.Model):
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente de Pago"),
        ("pagada", "Pagada"),
        ("anulada", "Anulada"),
    ]
    METODO_PAGO_CHOICES = [
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia Bancaria"),
        ("tarjeta", "Tarjeta Débito/Crédito"),
        ("credito", "Crédito"),
    ]
    
    numero = models.CharField(max_length=50, unique=True, editable=False)
    cotizacion = models.OneToOneField('cotizaciones.Cotizacion', on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name="venta")
    cliente_nombre = models.CharField(max_length=200)
    razon_social = models.CharField(max_length=200, blank=True)
    nit = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=300, blank=True)
    telefono = models.CharField(max_length=20)
    correo_electronico = models.EmailField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="pendiente")
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default="efectivo")
    fecha_venta = models.DateField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    notas = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-fecha_venta"]
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"

    def __str__(self):
        return f"Venta #{self.numero} - {self.cliente_nombre}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generar_numero()
        super().save(*args, **kwargs)

    @staticmethod
    def generar_numero():
        """Genera el siguiente número de venta automáticamente"""
        ultima = Venta.objects.all().order_by('-id').first()
        if ultima and ultima.numero.startswith('VNT-'):
            try:
                ultimo_numero = int(ultima.numero.split('-')[1])
                nuevo_numero = ultimo_numero + 1
            except (IndexError, ValueError):
                nuevo_numero = 1
        else:
            nuevo_numero = 1
        return f"VNT-{nuevo_numero:04d}"

    @property
    def subtotal(self):
        return sum(t.subtotal_tablero for t in self.tableros_venta.all())

    @property
    def iva(self):
        return int(self.subtotal * 19 / 100)

    @property
    def total(self):
        return self.subtotal + self.iva


class VentaTablero(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="tableros_venta")
    descripcion = models.TextField(blank=True, null=True)
    valor_tablero = models.PositiveIntegerField(default=0)
    descuento_tablero = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    descuento_materiales = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']
        verbose_name = "Item de Venta"
        verbose_name_plural = "Items de Venta"

    def __str__(self):
        return f"Item #{self.orden + 1} - {self.venta.numero}"

    @property
    def subtotal_tablero_bruto(self):
        return int(self.valor_tablero * (100 - self.descuento_tablero) / 100)

    @property
    def subtotal_materiales(self):
        total = sum(m.subtotal for m in self.materiales_venta.all())
        return int(total * (100 - self.descuento_materiales) / 100)

    @property
    def subtotal_tablero(self):
        return self.subtotal_tablero_bruto + self.subtotal_materiales


class VentaMaterial(models.Model):
    venta_tablero = models.ForeignKey(VentaTablero, on_delete=models.CASCADE, related_name="materiales_venta")
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