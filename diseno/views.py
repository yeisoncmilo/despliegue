from django.shortcuts import render, redirect, get_object_or_404
from produccion.models import OrdenProduccion
from .models import Diseno, ArchivoDiseno
from .forms import DisenoForm, ArchivoDisenoInlineFormSet

def lista_disenos(request):
    disenos = Diseno.objects.select_related('orden').all().order_by('-fecha_creacion')
    return render(request, "diseno/lista_disenos.html", {"disenos": disenos})

def nuevo_diseno(request):
    if request.method == "POST":
        form = DisenoForm(request.POST)
        formset = ArchivoDisenoInlineFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            diseno = form.save()
            formset.instance = diseno
            formset.save()
            return redirect("diseno:lista")
    else:
        form = DisenoForm()
        formset = ArchivoDisenoInlineFormSet()
    return render(request, "diseno/nuevo_diseno.html", {"form": form, "formset": formset})

def nuevo_diseno_orden(request, orden_pk):
    orden = get_object_or_404(OrdenProduccion, pk=orden_pk)
    if request.method == "POST":
        form = DisenoForm(request.POST)
        formset = ArchivoDisenoInlineFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            diseno = form.save(commit=False)
            diseno.orden = orden
            diseno.tipo = "orden"
            diseno.save()
            formset.instance = diseno
            formset.save()
            return redirect("produccion:detalle", pk=orden.pk)
    else:
        form = DisenoForm(initial={"orden": orden, "tipo": "orden"})
        formset = ArchivoDisenoInlineFormSet()
    return render(request, "diseno/nuevo_diseno.html", {"form": form, "formset": formset, "orden": orden})

def detalle_diseno(request, pk):
    diseno = get_object_or_404(Diseno, pk=pk)
    return render(request, "diseno/detalle_diseno.html", {"diseno": diseno})

def editar_diseno(request, pk):
    diseno = get_object_or_404(Diseno, pk=pk)
    if request.method == "POST":
        form = DisenoForm(request.POST, instance=diseno)
        formset = ArchivoDisenoInlineFormSet(request.POST, request.FILES, instance=diseno)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            if diseno.orden:
                return redirect("produccion:detalle", pk=diseno.orden.pk)
            return redirect("diseno:lista")
    else:
        form = DisenoForm(instance=diseno)
        formset = ArchivoDisenoInlineFormSet(instance=diseno)
    return render(request, "diseno/editar_diseno.html", {"form": form, "formset": formset, "diseno": diseno})

def eliminar_diseno(request, pk):
    diseno = get_object_or_404(Diseno, pk=pk)
    if request.method == "POST":
        orden_pk = diseno.orden.pk if diseno.orden else None
        diseno.delete()
        if orden_pk:
            return redirect("produccion:detalle", pk=orden_pk)
        return redirect("diseno:lista")
    return render(request, "diseno/eliminar_diseno.html", {"diseno": diseno})