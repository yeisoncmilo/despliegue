from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .models import OrdenProduccion, MaterialProduccion
from .forms import OrdenProduccionForm
from cotizaciones.models import Cotizacion

def lista_ordenes(request):
    ordenes = OrdenProduccion.objects.all().order_by("-fecha_creacion")
    return render(request, "produccion/lista_ordenes.html", {"ordenes": ordenes})

def nueva_orden(request):
    ultima_orden = OrdenProduccion.objects.all().order_by('-id').first()
    if ultima_orden and ultima_orden.numero.startswith('ORD-'):
        try:
            ultimo_numero = int(ultima_orden.numero.split('-')[1])
            nuevo_numero = ultimo_numero + 1
        except (IndexError, ValueError):
            nuevo_numero = 1
    else:
        nuevo_numero = 1
    numero_generado = f"ORD-{nuevo_numero:04d}"
    
    if request.method == "POST":
        form = OrdenProduccionForm(request.POST, request.FILES)
        if form.is_valid():
            orden = form.save()
            
            # Procesar materiales dinámicos (manualmente)
            material_indices = set()
            for key in request.POST.keys():
                if key.startswith('material_') and '_nombre' in key:
                    idx = key.split('_')[1]
                    material_indices.add(int(idx))
            
            for idx in sorted(material_indices):
                nombre = request.POST.get(f'material_{idx}_nombre', '').strip()
                
                if nombre and len(nombre) > 0:
                    cantidad = request.POST.get(f'material_{idx}_cantidad', 1)
                    
                    MaterialProduccion.objects.create(
                        orden=orden,
                        nombre=nombre,
                        cantidad=int(cantidad) if cantidad else 1
                    )
            
            messages.success(request, f'Orden de Producción {orden.numero} creada exitosamente.')
            return redirect("produccion:detalle", pk=orden.pk)
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = OrdenProduccionForm()
    
    cotizaciones = Cotizacion.objects.all().order_by("-id")
    return render(request, "produccion/nueva_orden.html", {
        "form": form,
        "cotizaciones": cotizaciones,
        "numero_generado": numero_generado
    })

def detalle_orden(request, pk):
    orden = get_object_or_404(OrdenProduccion, pk=pk)
    return render(request, "produccion/detalle_orden.html", {
        "orden": orden,
        "materiales": orden.materiales.all()
    })

def editar_orden(request, pk):
    orden = get_object_or_404(OrdenProduccion, pk=pk)
    
    if request.method == "POST":
        form = OrdenProduccionForm(request.POST, request.FILES, instance=orden)
        if form.is_valid():
            form.save()
            
            # Borrar y recrear materiales (como en cotizaciones)
            orden.materiales.all().delete()
            
            material_indices = set()
            for key in request.POST.keys():
                if key.startswith('material_') and '_nombre' in key:
                    idx = key.split('_')[1]
                    material_indices.add(int(idx))
            
            for idx in sorted(material_indices):
                nombre = request.POST.get(f'material_{idx}_nombre', '').strip()
                
                if nombre and len(nombre) > 0:
                    cantidad = request.POST.get(f'material_{idx}_cantidad', 1)
                    
                    MaterialProduccion.objects.create(
                        orden=orden,
                        nombre=nombre,
                        cantidad=int(cantidad) if cantidad else 1
                    )
            
            messages.success(request, 'Orden de Producción actualizada exitosamente.')
            return redirect("produccion:detalle", pk=orden.pk)
    else:
        form = OrdenProduccionForm(instance=orden)
    
    return render(request, "produccion/editar_orden.html", {
        "form": form,
        "orden": orden
    })

def eliminar_orden(request, pk):
    orden = get_object_or_404(OrdenProduccion, pk=pk)
    if request.method == "POST":
        numero = orden.numero
        orden.delete()
        messages.success(request, f'Orden de Producción {numero} eliminada exitosamente.')
        return redirect("produccion:lista")
    return render(request, "produccion/eliminar.html", {"orden": orden})

def cargar_cotizacion(request, pk):
    """AJAX endpoint para cargar datos desde cotización"""
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    return JsonResponse({
        'cliente_nombre': cotizacion.cliente_nombre,
        'razon_social': cotizacion.razon_social or '',
        'telefono': cotizacion.telefono,
        'correo_electronico': cotizacion.correo_electronico,
        'nit': cotizacion.nit or '',
        'direccion': cotizacion.direccion or '',
        'descripcion': cotizacion.descripcion or '',
        'materiales': list(cotizacion.material_set.values('nombre', 'cantidad')) if hasattr(cotizacion, 'material_set') else []
    })