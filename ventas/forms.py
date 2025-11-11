from django import forms
from django.forms import inlineformset_factory
from .models import Venta, DetalleVenta


class VentaForm(forms.ModelForm):
    class Meta:
        model  = Venta
        fields = ["numero", "cliente_nombre", "razon_social", "telefono",
                  "correo", "direccion_envio", "estado"]
        widgets = {
            "numero":          forms.TextInput(attrs={"class": "form-control"}),
            "cliente_nombre":  forms.TextInput(attrs={"class": "form-control"}),
            "razon_social":    forms.TextInput(attrs={"class": "form-control"}),
            "telefono":        forms.TextInput(attrs={"class": "form-control"}),
            "correo":          forms.EmailInput(attrs={"class": "form-control"}),
            "direccion_envio": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "estado":          forms.Select(attrs={"class": "form-select"}),
        }


class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model  = DetalleVenta
        fields = ["descripcion", "cantidad", "precio_unit", "descuento"]
        widgets = {
            "descripcion": forms.TextInput(attrs={"class": "form-control"}),
            "cantidad":    forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "precio_unit": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "descuento":   forms.NumberInput(attrs={"class": "form-control", "step": "0.1", "min": 0, "max": 100}),
        }


DetalleVentaFormSet = inlineformset_factory(
    Venta,
    DetalleVenta,
    form=DetalleVentaForm,
    extra=1,
    can_delete=True,
)