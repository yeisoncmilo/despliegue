from django.urls import path
from . import views

app_name = "diseno"

urlpatterns = [
    path("", views.lista_disenos, name="lista"),
    path("nuevo/", views.nuevo_diseno, name="nuevo_sin_orden"),  
    path("nuevo/<int:orden_pk>/", views.nuevo_diseno_orden, name="nuevo"),  
    path("<int:pk>/", views.detalle_diseno, name="detalle"),
    path("<int:pk>/editar/", views.editar_diseno, name="editar"),
    path("<int:pk>/eliminar/", views.eliminar_diseno, name="eliminar"),
]