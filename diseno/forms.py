from django import forms
from django.forms import inlineformset_factory
from .models import Diseno, ArchivoDiseno, OrdenProduccion

class DisenoForm(forms.ModelForm):
    class Meta:
        model = Diseno
        fields = ["numero", "nombre", "descripcion", "tipo", "orden"]
        widgets = {
            "numero": forms.TextInput(attrs={"class": "form-control"}),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "orden": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar órdenes que aún no tengan diseño (opcional)
        self.fields["orden"].queryset = OrdenProduccion.objects.filter(disenos__isnull=True).order_by('-fecha_creacion')
        self.fields["orden"].empty_label = "Ninguna (diseño libre)"


ArchivoDisenoInlineFormSet = inlineformset_factory(
    Diseno,
    ArchivoDiseno,
    fields=["archivo"],
    extra=1,
    can_delete=True,
    widgets={
        "archivo": forms.FileInput(attrs={"class": "form-control"}),
    },
)