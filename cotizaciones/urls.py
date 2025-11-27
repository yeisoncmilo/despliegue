from django.urls import path
from . import views

app_name = "cotizaciones"

urlpatterns = [
    path("", views.lista_cotizaciones, name="lista"),
    path("crear/", views.nueva_cotizacion, name="crear"),
    path("<int:pk>/", views.detalle_cotizacion, name="detalle"),
    path("<int:pk>/editar/", views.editar_cotizacion, name="editar"),
    path("<int:pk>/eliminar/", views.eliminar_cotizacion, name="eliminar"),
    path("<int:pk>/cambiar-estado/", views.cambiar_estado_cotizacion, name="cambiar_estado"),
    path('pdf/<int:pk>/', views.generar_pdf_cotizacion, name='pdf'),
    path('<int:pk>/enviar-correo/', views.enviar_cotizacion_correo, name='enviar_correo'),
]