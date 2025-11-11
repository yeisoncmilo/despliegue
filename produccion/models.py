from django.db import models
from django.core.validators import MinValueValidator
from cotizaciones.models import Cotizacion

class OrdenProduccion(models.Model):
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("en_proceso", "En proceso"),
        ("finalizada", "Finalizada"),
    ]

    numero = models.CharField(max_length=50, unique=True, editable=False)
    cliente_nombre = models.CharField(max_length=200)
    razon_social = models.CharField(max_length=200)
    nit = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=300, blank=True)
    telefono = models.CharField(max_length=20)
    correo_electronico = models.EmailField()
    tipo_tablero = models.CharField(max_length=200)
    dimensiones = models.CharField(max_length=200)
    color = models.CharField(max_length=100)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="pendiente")
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.SET_NULL, null=True, blank=True)
    archivo = models.FileField(upload_to='ordenes_archivos/%Y/%m/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"Orden #{self.numero} - {self.cliente_nombre}"

    def save(self, *args, **kwargs):
        if not self.numero:
            # Generar número automático secuencial
            ultima_orden = OrdenProduccion.objects.all().order_by('-id').first()
            if ultima_orden and ultima_orden.numero.startswith('ORD-'):
                try:
                    ultimo_numero = int(ultima_orden.numero.split('-')[1])
                    nuevo_numero = ultimo_numero + 1
                except (IndexError, ValueError):
                    nuevo_numero = 1
            else:
                nuevo_numero = 1
            self.numero = f"ORD-{nuevo_numero:04d}"
        super().save(*args, **kwargs)


class MaterialProduccion(models.Model):
    orden = models.ForeignKey(OrdenProduccion, on_delete=models.CASCADE, related_name="materiales")
    nombre = models.CharField(max_length=200)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.nombre} ({self.cantidad})"