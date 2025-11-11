
from django import forms
from django.contrib.auth.forms import AuthenticationForm

class FormularioLoginPersonalizado(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Usuario'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Contraseña'
    }))
    rol = forms.ChoiceField(
        choices=[
            ('admin', 'Administrador'),
            ('ventas', 'Ventas'),
            ('produccion', 'Producción'),
            ('diseno', 'Diseño'),
            ('cotizaciones', 'Cotizaciones'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Selecciona tu rol'
        }),
        required=True
    )