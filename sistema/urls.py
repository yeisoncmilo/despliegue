from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

# Import correcto de las vistas
from autenticacion.views import (
    vista_login,
    vista_logout,
    dashboard,
    busqueda_global,   # <-- Faltaba
    perfil_usuario,
    cambiar_contrasena,
    configuracion,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticación
    path('login/', vista_login, name='login'),
    path('logout/', vista_logout, name='logout'),

    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),

    # Búsqueda global
    path('busqueda/', busqueda_global, name='busqueda_global'),

    # Perfil y configuraciones
    path('perfil/', perfil_usuario, name='perfil'),
    path('cambiar-contrasena/', cambiar_contrasena, name='cambiar_contrasena'),
    path('configuracion/', configuracion, name='configuracion'),

    # Apps principales
    path('cotizaciones/', include('cotizaciones.urls')),
    path('ventas/', include('ventas.urls')),
    path('produccion/', include('produccion.urls')),
    path('diseno/', include('diseno.urls')),
    path('api/', include('api.urls')),

    # Redirección raíz → login
    path('', lambda request: redirect('login'), name='home'),
]

# Servir archivos MEDIOS
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
