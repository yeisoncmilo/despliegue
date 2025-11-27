from rest_framework import serializers
from .models import Cotizacion, Tablero, Material

class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ['nombre', 'cantidad', 'valor_unitario', 'descuento', 'subtotal']

class TableroSerializer(serializers.ModelSerializer):
    materiales = MaterialSerializer(many=True, read_only=True)

    class Meta:
        model = Tablero
        fields = ['descripcion', 'valor_tablero', 'descuento_tablero', 'descuento_materiales', 'subtotal_tablero', 'materiales']

class CotizacionSerializer(serializers.ModelSerializer):
    tableros = TableroSerializer(many=True, read_only=True)

    class Meta:
        model = Cotizacion
        fields = ['numero', 'cliente_nombre', 'correo_electronico', 'estado', 'fecha_creacion', 'subtotal', 'iva', 'total', 'tableros']