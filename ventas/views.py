from django.shortcuts import render, redirect, get_object_or_404
from .models import Venta
from .forms import VentaForm, DetalleVentaFormSet


def lista_ventas(request):
    ventas = Venta.objects.all()
    return render(request, "ventas/lista_ventas.html", {"ventas": ventas})


def nueva_venta(request):
    if request.method == "POST":
        form, formset = VentaForm(request.POST), DetalleVentaFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            venta = form.save()
            formset.instance = venta
            formset.save()
            venta.save()  # calcula totales + API
            return redirect("ventas:detalle", pk=venta.pk)
    else:
        form, formset = VentaForm(), DetalleVentaFormSet()
    return render(request, "ventas/nueva_venta.html", {"form": form, "formset": formset})


def detalle_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    return render(request, "ventas/detalle_venta.html", {"venta": venta})


def editar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == "POST":
        form, formset = VentaForm(request.POST, instance=venta), DetalleVentaFormSet(request.POST, instance=venta)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            venta.save()  # recalcula + API sólo si está vacío
            return redirect("ventas:detalle", pk=venta.pk)
    else:
        form, formset = VentaForm(instance=venta), DetalleVentaFormSet(instance=venta)
    return render(request, "ventas/editar_venta.html", {"form": form, "formset": formset, "venta": venta})


def eliminar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == "POST":
        venta.delete()
        return redirect("ventas:lista")
    return render(request, "ventas/eliminar_venta.html", {"venta": venta})