from django.urls import path
from .views import CotizacionesAprobadasAPI

urlpatterns = [
    path('cotizaciones-aprobadas/', CotizacionesAprobadasAPI.as_view(), name='cotizaciones_aprobadas'),
]