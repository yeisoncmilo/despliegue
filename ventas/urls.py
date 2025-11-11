from django.urls import path
from . import views

app_name = "ventas"

urlpatterns = [
    path("", views.lista_ventas, name="lista"),
    path("nueva/", views.nueva_venta, name="nueva"),
    path("<int:pk>/", views.detalle_venta, name="detalle"),
    path("<int:pk>/editar/", views.editar_venta, name="editar"),
    path("<int:pk>/eliminar/", views.eliminar_venta, name="eliminar"),
]