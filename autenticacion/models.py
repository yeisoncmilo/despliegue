from django.db import models
from django.contrib.auth.models import AbstractUser

class UsuarioPersonalizado(AbstractUser):
    ROLES =(
        ('admin', 'Administrador'),
        ('ventas', 'Ventas'),
        ('cotizaciones', 'Cotizaciones'),
        ('produccion', 'Produccion'),
        ('diseño', 'Diseno'),

    )

    rol = models.CharField(max_length=20, choices=ROLES, default='admin')
    telefono = models.CharField(max_length=15, blank=True)
    departamento = models.CharField(max_length=50, blank=True)


    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"
    
    

