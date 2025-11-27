from django import forms
from .models import OrdenProduccion, MaterialProduccion

class OrdenProduccionForm(forms.ModelForm):
    class Meta:
        model = OrdenProduccion
        fields = [
            "cliente_nombre", "razon_social", "nit", "direccion",
            "telefono", "correo_electronico", "tipo_tablero", "dimensiones",
            "color", "observaciones", "estado", "cotizacion", "archivo"
        ]
        widgets = {
            "cliente_nombre": forms.TextInput(attrs={"class": "form-control"}),
            "razon_social": forms.TextInput(attrs={"class": "form-control"}),
            "nit": forms.TextInput(attrs={"class": "form-control"}),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "correo_electronico": forms.EmailInput(attrs={"class": "form-control"}),
            "tipo_tablero": forms.TextInput(attrs={"class": "form-control"}),
            "dimensiones": forms.TextInput(attrs={"class": "form-control"}),
            "color": forms.TextInput(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Notas adicionales..."}),
            "estado": forms.Select(attrs={"class": "form-select"}),
            "cotizacion": forms.Select(attrs={"class": "form-select", "data-cotizacion-select": "true"}),
            "archivo": forms.FileInput(attrs={"class": "form-control", "accept": ".pdf,.jpg,.png,.dwg,.dxf"}),
        }

class MaterialProduccionForm(forms.ModelForm):
    class Meta:
        model = MaterialProduccion
        fields = ["nombre", "cantidad"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }