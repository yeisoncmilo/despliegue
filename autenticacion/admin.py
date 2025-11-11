from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioPersonalizado

class UsuarioPersonalizadoAdmin(UserAdmin):
    model = UsuarioPersonalizado
    list_display = ['username', 'email', 'rol', 'is_active']
    fieldsets = UserAdmin.fieldsets + (('Informacion adicional',{'fields':('rol', 'telefono', 'departamento')}),
    )

admin.site.register(UsuarioPersonalizado, UsuarioPersonalizadoAdmin)