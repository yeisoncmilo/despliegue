from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from autenticacion.views import vista_login, vista_logout, dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', vista_login, name='login'),
    path('logout/', vista_logout, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('cotizaciones/', include('cotizaciones.urls')),
    #path('ventas/', include('ventas.urls')),
    path('produccion/', include('produccion.urls')),
    path('diseno/', include('diseno.urls')),
    # Redireccionar la URL raíz al login
    path('', lambda request: redirect('login'), name='home'),
]

# Servir archivos MEDIA en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)