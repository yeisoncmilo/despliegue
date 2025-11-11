from django.db import models
from django.core.validators import FileExtensionValidator
from produccion.models import OrdenProduccion

TIPO_CHOICES = [
    ("orden", "Vinculado a Orden"),
    ("libre", "Independiente / Cliente"),
]

class Diseno(models.Model):
    numero = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default="libre")
    orden = models.ForeignKey(
        OrdenProduccion,
        on_delete=models.CASCADE,
        related_name="disenos",
        null=True,
        blank=True,
        help_text="Dejar vacío para diseños independientes o prediseños"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "Diseño"
        verbose_name_plural = "Diseños"

    def __str__(self):
        if self.orden:
            return f"Diseño #{self.numero} - Orden #{self.orden.numero}"
        return f"Diseño #{self.numero} - {self.nombre} (Libre)"


class ArchivoDiseno(models.Model):
    diseno = models.ForeignKey(Diseno, on_delete=models.CASCADE, related_name="archivos")
    archivo = models.FileField(
        upload_to="disenos/archivos/",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'dwg', 'jpg', 'jpeg', 'png', 'svg'])]
    )
    nombre = models.CharField(max_length=200, blank=True)

    def save(self, *args, **kwargs):
        if not self.nombre and self.archivo:
            self.nombre = self.archivo.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre