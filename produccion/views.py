from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.conf import settings
from django.core.mail import EmailMessage
from io import BytesIO
import logging
import os

from .models import OrdenProduccion, MaterialProduccion
from .forms import OrdenProduccionForm
from cotizaciones.models import Cotizacion

logger = logging.getLogger(__name__)

@login_required
def lista_ordenes(request):
    ordenes = OrdenProduccion.objects.all().order_by('-fecha_creacion')
    return render(request, 'produccion/lista_ordenes.html', {
        'ordenes': ordenes
    })

@login_required
def detalle_orden(request, pk):
    orden = get_object_or_404(OrdenProduccion, pk=pk)
    materiales = orden.materiales.all()
    
    context = {
        'orden': orden,
        'materiales': materiales,
    }
    return render(request, 'produccion/detalle_orden.html', context)

def procesar_materiales(orden, post_data):
    orden.materiales.all().delete()
    
    material_indices = set()
    for key in post_data.keys():
        if key.startswith('material_') and '_nombre' in key:
            idx = key.split('_')[1]
            if idx.isdigit():
                material_indices.add(int(idx))
    
    for idx in sorted(material_indices):
        nombre = post_data.get(f'material_{idx}_nombre', '').strip()
        if not nombre:
            continue
            
        cantidad = int(post_data.get(f'material_{idx}_cantidad', 1) or 1)
        
        MaterialProduccion.objects.create(
            orden=orden,
            nombre=nombre,
            cantidad=cantidad
        )

@login_required
def nueva_orden(request):
    if request.method == 'POST':
        form = OrdenProduccionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    orden = form.save(commit=False)
                    orden.numero = OrdenProduccion.generar_numero()
                    orden.save()
                    
                    procesar_materiales(orden, request.POST)
                    
                    messages.success(request, f"✅ Orden #{orden.numero} creada exitosamente.")
                    return redirect('produccion:detalle', pk=orden.pk)
            except Exception as e:
                logger.error(f"Error al crear orden: {str(e)}", exc_info=True)
                messages.error(request, f"❌ Error al guardar la orden: {str(e)}")
        else:
            messages.error(request, "❌ Por favor, corrige los errores en el formulario.")
    else:
        form = OrdenProduccionForm()
        numero_generado = OrdenProduccion.generar_numero()

    cotizaciones = Cotizacion.objects.all().order_by('-fecha_creacion')
    return render(request, 'produccion/nueva_orden.html', {
        'form': form,
        'numero_generado': numero_generado,
        'cotizaciones': cotizaciones
    })

@login_required
def editar_orden(request, pk):
    orden = get_object_or_404(OrdenProduccion, pk=pk)
    
    if request.method == 'POST':
        form = OrdenProduccionForm(request.POST, request.FILES, instance=orden)
        if form.is_valid():
            try:
                with transaction.atomic():
                    orden = form.save()
                    procesar_materiales(orden, request.POST)
                    
                    messages.success(request, f"✅ Orden #{orden.numero} actualizada correctamente.")
                    return redirect('produccion:detalle', pk=orden.pk)
            except Exception as e:
                logger.error(f"Error al editar orden {pk}: {str(e)}", exc_info=True)
                messages.error(request, f"❌ Error al actualizar la orden: {str(e)}")
        else:
            messages.error(request, "❌ Corrige los errores antes de guardar.")
    else:
        form = OrdenProduccionForm(instance=orden)

    return render(request, 'produccion/editar_orden.html', {
        'form': form, 
        'orden': orden
    })

@login_required
def eliminar_orden(request, pk):
    orden = get_object_or_404(OrdenProduccion, pk=pk)

    if request.method == 'POST':
        numero = orden.numero
        try:
            orden.delete()
            messages.success(request, f"🗑️ Orden #{numero} eliminada correctamente.")
        except Exception as e:
            logger.error(f"Error al eliminar orden {pk}: {str(e)}")
            messages.error(request, "❌ Error al eliminar la orden.")
        return redirect('produccion:lista')

    return render(request, 'produccion/eliminar.html', {'orden': orden})

@login_required
def cargar_cotizacion(request, pk):
    try:
        cotizacion = get_object_or_404(Cotizacion, pk=pk)
        
        materiales = []
        for tablero in cotizacion.tableros.all():
            for material in tablero.materiales.all():
                materiales.append({
                    'nombre': material.nombre,
                    'cantidad': material.cantidad
                })
        
        return JsonResponse({
            'cliente_nombre': cotizacion.cliente_nombre,
            'razon_social': cotizacion.razon_social or '',
            'nit': cotizacion.nit or '',
            'direccion': cotizacion.direccion or '',
            'telefono': cotizacion.telefono,
            'correo_electronico': cotizacion.correo_electronico,
            'materiales': materiales
        })
    except Exception as e:
        logger.error(f"Error en AJAX cargar cotización: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def generar_pdf_orden(request, pk, to_buffer=None):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    
    orden = get_object_or_404(OrdenProduccion, pk=pk)
    materiales = orden.materiales.all()
    
    if to_buffer:
        buffer = to_buffer
    else:
        buffer = BytesIO()
    
    try:
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                               title=f"Orden de Producción {orden.numero}")
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#28a745'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        title = Paragraph(f"ORDEN DE PRODUCCIÓN #{orden.numero}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        cliente_data = [
            ['INFORMACIÓN DEL CLIENTE', ''],
            ['Nombre:', orden.cliente_nombre],
            ['Razón Social:', orden.razon_social or '-'],
            ['NIT:', orden.nit or '-'],
            ['Dirección:', orden.direccion or '-'],
            ['Teléfono:', orden.telefono],
            ['Email:', orden.correo_electronico],
            ['Fecha:', orden.fecha_creacion.strftime('%d/%m/%Y')],
        ]
        
        cliente_table = Table(cliente_data, colWidths=[2*inch, 4*inch])
        cliente_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(cliente_table)
        elements.append(Spacer(1, 0.3*inch))
        
        detalles_data = [
            ['DETALLES DE LA ORDEN', ''],
            ['Tipo de Tablero:', orden.tipo_tablero],
            ['Dimensiones:', orden.dimensiones],
            ['Color:', orden.color],
            ['Estado:', orden.get_estado_display().upper()],
        ]
        
        if orden.cotizacion:
            detalles_data.append(['Cotización Relacionada:', f"#{orden.cotizacion.numero}"])
        
        detalles_table = Table(detalles_data, colWidths=[2*inch, 4*inch])
        detalles_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17a2b8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(detalles_table)
        elements.append(Spacer(1, 0.3*inch))
        
        if materiales.exists():
            materiales_header = Paragraph("<b>MATERIALES REQUERIDOS</b>", styles['Heading2'])
            elements.append(materiales_header)
            elements.append(Spacer(1, 0.1*inch))
            
            materiales_data = [['Material', 'Cantidad']]
            for material in materiales:
                materiales_data.append([material.nombre, str(material.cantidad)])
            
            materiales_table = Table(materiales_data, colWidths=[4*inch, 2*inch])
            materiales_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(materiales_table)
        
        if orden.observaciones:
            elements.append(Spacer(1, 0.3*inch))
            obs_header = Paragraph("<b>OBSERVACIONES</b>", styles['Heading2'])
            elements.append(obs_header)
            obs_text = Paragraph(orden.observaciones.replace('\n', '<br/>'), styles['Normal'])
            elements.append(obs_text)
        
        doc.build(elements)
        
    except Exception as e:
        logger.error(f"Error al generar PDF para orden {pk}: {str(e)}", exc_info=True)
        raise
    
    if to_buffer:
        return buffer
    else:
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Orden_{orden.numero}.pdf"'
        return response

@login_required
def enviar_orden_correo(request, pk):
    orden = get_object_or_404(OrdenProduccion, pk=pk)
    
    if not orden.correo_electronico:
        messages.error(request, "❌ La orden no tiene un correo electrónico asociado.")
        return redirect("produccion:detalle", pk=pk)
    
    try:
        pdf_buffer = BytesIO()
        generar_pdf_orden(request, pk, to_buffer=pdf_buffer)
        pdf_data = pdf_buffer.getvalue()
        
        if not pdf_data or len(pdf_data) < 1000:
            raise ValueError("El PDF generado está vacío o corrupto")
        
        asunto = f"Orden de Producción {orden.numero} - SynCroPro"
        mensaje = f"""Hola {orden.cliente_nombre},

Le enviamos la orden de producción número {orden.numero}.

Tipo de tablero: {orden.tipo_tablero}
Dimensiones: {orden.dimensiones}
Color: {orden.color}
Estado: {orden.get_estado_display()}

Adjunto encontrará el archivo PDF con los detalles completos.

Atentamente,
El equipo de SynCroPro
"""
        
        from_email = settings.DEFAULT_FROM_EMAIL
        
        email = EmailMessage(
            subject=asunto,
            body=mensaje,
            from_email=from_email,
            to=[orden.correo_electronico],
            reply_to=[from_email],
        )
        
        nombre_archivo = f"Orden_{orden.numero}.pdf"
        email.attach(nombre_archivo, pdf_data, "application/pdf")
        
        email.send(fail_silently=False)
        
        logger.info(f"Orden {orden.numero} enviada exitosamente a {orden.correo_electronico}")
        messages.success(request, f"✅ Orden enviada exitosamente a {orden.correo_electronico}")
        
    except Exception as e:
        logger.error(f"Error al enviar orden {pk}: {str(e)}", exc_info=True)
        messages.error(request, f"❌ Error al enviar el correo: {str(e)}")
    
    finally:
        if 'pdf_buffer' in locals():
            pdf_buffer.close()
    
    return redirect("produccion:detalle", pk=pk)