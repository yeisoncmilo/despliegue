from django.urls import path
from . import views

app_name = "ventas"

urlpatterns = [
    path("", views.lista_ventas, name="lista"),
    path("crear/", views.crear_venta, name="crear"),
    path("crear/<int:cotizacion_pk>/", views.crear_venta, name="crear_desde_cotizacion"),
    path("<int:pk>/", views.detalle_venta, name="detalle"),
    path("<int:pk>/editar/", views.editar_venta, name="editar"),
    path("<int:pk>/eliminar/", views.eliminar_venta, name="eliminar"),
    path('<int:pk>/pdf/', views.generar_pdf_venta, name='pdf'),
    path('<int:pk>/enviar-correo/', views.enviar_venta_correo, name='enviar_correo'),
    path('convertir-cotizacion/<int:cotizacion_pk>/', views.convertir_cotizacion_a_venta, name='convertir_cotizacion'),
    # **NUEVA RUTA:**
    path('ajax/cargar-cotizacion/<int:pk>/', views.cargar_cotizacion, name='ajax_cargar_cotizacion'),
]