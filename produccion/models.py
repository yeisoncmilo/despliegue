from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from cotizaciones.models import Cotizacion

class OrdenProduccion(models.Model):
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("en_proceso", "En proceso"),
        ("finalizada", "Finalizada"),
        ("cancelada", "Cancelada"),
    ]

    numero = models.CharField(max_length=50, unique=True, editable=False)
    cliente_nombre = models.CharField(max_length=200, verbose_name="Nombre del Cliente")
    razon_social = models.CharField(max_length=200, blank=True, verbose_name="Razón Social")
    nit = models.CharField(max_length=20, blank=True, verbose_name="NIT")
    direccion = models.CharField(max_length=300, blank=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    correo_electronico = models.EmailField(verbose_name="Correo Electrónico")
    tipo_tablero = models.CharField(max_length=200, verbose_name="Tipo de Tablero")
    dimensiones = models.CharField(max_length=200, verbose_name="Dimensiones")
    color = models.CharField(max_length=100, verbose_name="Color")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cotización Relacionada")
    archivo = models.FileField(upload_to='ordenes_archivos/%Y/%m/', blank=True, null=True, verbose_name="Archivo Adjunto (Plano, PDF, etc.)")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="pendiente", verbose_name="Estado")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "Orden de Producción"
        verbose_name_plural = "Órdenes de Producción"

    def __str__(self):
        return f"Orden #{self.numero} - {self.cliente_nombre}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generar_numero()
        super().save(*args, **kwargs)

    @staticmethod
    def generar_numero():
        ultima = OrdenProduccion.objects.all().order_by('-id').first()
        if ultima and ultima.numero.startswith('ORD-'):
            try:
                ultimo_numero = int(ultima.numero.split('-')[1])
                nuevo_numero = ultimo_numero + 1
            except (IndexError, ValueError):
                nuevo_numero = 1
        else:
            nuevo_numero = 1
        return f"ORD-{nuevo_numero:04d}"

    @property
    def total_materiales(self):
        return self.materiales.count()

    def get_materiales_list(self):
        return ", ".join([f"{m.nombre} ({m.cantidad})" for m in self.materiales.all()])


class MaterialProduccion(models.Model):
    orden = models.ForeignKey(OrdenProduccion, on_delete=models.CASCADE, related_name="materiales", verbose_name="Orden de Producción")
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Material")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")

    class Meta:
        verbose_name = "Material de Producción"
        verbose_name_plural = "Materiales de Producción"

    def __str__(self):
        return f"{self.nombre} - {self.cantidad} unidades"