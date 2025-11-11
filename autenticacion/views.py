from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import FormularioLoginPersonalizado
from .models import UsuarioPersonalizado

def vista_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = FormularioLoginPersonalizado(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            rol_seleccionado = form.cleaned_data.get('rol')
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Verificar que el rol seleccionado coincida con el del usuario
                if user.rol == rol_seleccionado or user.rol == 'admin':
                    login(request, user)
                    return redirect('dashboard')
                else:
                    messages.error(request, 'El rol seleccionado no coincide con tu usuario')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = FormularioLoginPersonalizado()
    
    return render(request, 'autenticacion/login.html', {'form': form})

def vista_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'autenticacion/dashboard.html')