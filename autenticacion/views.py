from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import FormularioLoginPersonalizado
from .models import UsuarioPersonalizado
from django.contrib.auth.forms import PasswordChangeForm

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

@login_required
def busqueda_global(request):
    """Vista para la búsqueda global del sistema"""
    query = request.GET.get('q', '').strip()
    resultados = {
        'cotizaciones': [],
        'ordenes_produccion': [],
        'proyectos_diseno': [],
        'ventas': [],
        'usuarios': []
    }
    
    if query:
        # Importar modelos según los tengas en tu proyecto
        try:
            from cotizaciones.models import Cotizacion
            resultados['cotizaciones'] = Cotizacion.objects.filter(
                Q(numero_cotizacion__icontains=query) |
                Q(cliente__icontains=query) |
                Q(descripcion__icontains=query)
            )[:5]
        except:
            pass
        
        try:
            from produccion.models import OrdenProduccion
            resultados['ordenes_produccion'] = OrdenProduccion.objects.filter(
                Q(numero_orden__icontains=query) |
                Q(cliente__icontains=query) |
                Q(descripcion__icontains=query)
            )[:5]
        except:
            pass
        
        try:
            from diseno.models import ProyectoDiseno
            resultados['proyectos_diseno'] = ProyectoDiseno.objects.filter(
                Q(nombre__icontains=query) |
                Q(descripcion__icontains=query)
            )[:5]
        except:
            pass
        
        try:
            from ventas.models import Venta
            resultados['ventas'] = Venta.objects.filter(
                Q(numero_factura__icontains=query) |
                Q(cliente__icontains=query)
            )[:5]
        except:
            pass
        
        # Búsqueda de usuarios (solo para admins)
        if request.user.rol == 'admin':
            resultados['usuarios'] = UsuarioPersonalizado.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            ).exclude(id=request.user.id)[:5]
    
    return render(request, 'autenticacion/resultados_busqueda.html', {
        'query': query,
        'resultados': resultados
    })

@login_required
def perfil_usuario(request):
    """Vista para ver/editar el perfil del usuario"""
    usuario = request.user
    
    if request.method == 'POST':
        # Actualizar datos del perfil
        usuario.first_name = request.POST.get('first_name', '')
        usuario.last_name = request.POST.get('last_name', '')
        usuario.email = request.POST.get('email', '')
        usuario.telefono = request.POST.get('telefono', '')
        usuario.departamento = request.POST.get('departamento', '')
        usuario.save()
        
        messages.success(request, 'Perfil actualizado correctamente')
        return redirect('perfil')
    
    return render(request, 'autenticacion/perfil.html', {'usuario': usuario})

@login_required
def cambiar_contrasena(request):
    """Vista para cambiar la contraseña del usuario"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Contraseña cambiada correctamente')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor corrige los errores')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'autenticacion/cambiar_contrasena.html', {'form': form})

@login_required
def configuracion(request):
    """Vista para configuraciones del usuario"""
    return render(request, 'autenticacion/configuracion.html')