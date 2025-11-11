from django.urls import path
from . import views

app_name = "produccion"

urlpatterns = [
    # CRUD de órdenes de producción
    path("", views.lista_ordenes, name="lista"),
    path("crear/", views.nueva_orden, name="crear"),
    path("<int:pk>/", views.detalle_orden, name="detalle"),
    path("<int:pk>/editar/", views.editar_orden, name="editar"),
    path("<int:pk>/eliminar/", views.eliminar_orden, name="eliminar"),

    # AJAX: cargar datos de cotización
    path('ajax/cargar-cotizacion/<int:pk>/', views.cargar_cotizacion, name='ajax_cargar_cotizacion'),
]