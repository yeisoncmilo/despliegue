from django.core.mail import EmailMessage
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db import transaction
from io import BytesIO
import logging
import os
from .models import Cotizacion, Tablero, Material
from .forms import CotizacionForm

logger = logging.getLogger(__name__)

@login_required
def lista_cotizaciones(request):
    cotizaciones = Cotizacion.objects.all().order_by('-fecha_creacion')
    return render(request, 'cotizaciones/lista_cotizaciones.html', {'cotizaciones': cotizaciones})

def generar_numero_cotizacion():
    ultima = Cotizacion.objects.all().order_by('-id').first()
    if ultima and ultima.numero.startswith('COT-'):
        try:
            ultimo_numero = int(ultima.numero.split('-')[1])
            nuevo_numero = ultimo_numero + 1
        except (IndexError, ValueError):
            nuevo_numero = 1
    else:
        nuevo_numero = 1
    return f"COT-{nuevo_numero:04d}"

def procesar_tableros_materiales(cotizacion, post_data):
    cotizacion.tableros.all().delete()
    tablero_indices = set()
    for key in post_data.keys():
        if key.startswith('tablero_') and '_descripcion' in key:
            idx = key.split('_')[1]
            if idx.isdigit():
                tablero_indices.add(int(idx))
    for idx in sorted(tablero_indices):
        descripcion = post_data.get(f'tablero_{idx}_descripcion', '').strip()
        if not descripcion:
            continue
        valor_tablero = int(post_data.get(f'tablero_{idx}_valor_tablero', 0) or 0)
        descuento_tablero = int(post_data.get(f'tablero_{idx}_descuento_tablero', 0) or 0)
        descuento_materiales = int(post_data.get(f'tablero_{idx}_descuento_materiales', 0) or 0)
        tablero = Tablero.objects.create(
            cotizacion=cotizacion,
            descripcion=descripcion,
            valor_tablero=valor_tablero,
            descuento_tablero=descuento_tablero,
            descuento_materiales=descuento_materiales,
            orden=idx
        )
        material_indices = set()
        for key in post_data.keys():
            if key.startswith(f'tablero_{idx}_material_') and '_nombre' in key:
                parts = key.split('_')
                if len(parts) >= 5 and parts[3].isdigit():
                    material_indices.add(int(parts[3]))
        for mat_idx in sorted(material_indices):
            nombre = post_data.get(f'tablero_{idx}_material_{mat_idx}_nombre', '').strip()
            if not nombre:
                continue
            cantidad = int(post_data.get(f'tablero_{idx}_material_{mat_idx}_cantidad', 1) or 1)
            valor_unitario = int(post_data.get(f'tablero_{idx}_material_{mat_idx}_valor_unitario', 0) or 0)
            descuento = int(post_data.get(f'tablero_{idx}_material_{mat_idx}_descuento', 0) or 0)
            Material.objects.create(
                tablero=tablero,
                nombre=nombre,
                cantidad=cantidad,
                valor_unitario=valor_unitario,
                descuento=descuento
            )

@login_required
def nueva_cotizacion(request):
    numero_generado = generar_numero_cotizacion()
    if request.method == 'POST':
        form = CotizacionForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    cotizacion = form.save(commit=False)
                    cotizacion.numero = numero_generado
                    cotizacion.save()
                    procesar_tableros_materiales(cotizacion, request.POST)
                    messages.success(request, f"✅ Cotización #{cotizacion.numero} creada exitosamente.")
                    return redirect('cotizaciones:detalle', pk=cotizacion.pk)
            except Exception as e:
                logger.error(f"Error al crear cotización: {str(e)}", exc_info=True)
                messages.error(request, f"❌ Error al guardar la cotización: {str(e)}")
        else:
            messages.error(request, "❌ Por favor, corrige los errores en el formulario.")
    else:
        form = CotizacionForm()
    return render(request, 'cotizaciones/nueva_cotizacion.html', {'form': form, 'numero_generado': numero_generado})

@login_required
def detalle_cotizacion(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    tableros = cotizacion.tableros.all()
    return render(request, 'cotizaciones/detalle_cotizacion.html', {
        'cotizacion': cotizacion,
        'tableros': tableros,
        'subtotal': cotizacion.subtotal,
        'iva': cotizacion.iva,
        'total': cotizacion.total,
    })

@login_required
def editar_cotizacion(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    if request.method == 'POST':
        form = CotizacionForm(request.POST, instance=cotizacion)
        if form.is_valid():
            try:
                with transaction.atomic():
                    cotizacion = form.save()
                    procesar_tableros_materiales(cotizacion, request.POST)
                    messages.success(request, f"✅ Cotización #{cotizacion.numero} actualizada correctamente.")
                    return redirect('cotizaciones:detalle', pk=cotizacion.pk)
            except Exception as e:
                logger.error(f"Error al editar cotización {pk}: {str(e)}", exc_info=True)
                messages.error(request, f"❌ Error al actualizar la cotización: {str(e)}")
        else:
            messages.error(request, "❌ Corrige los errores antes de guardar.")
    else:
        form = CotizacionForm(instance=cotizacion)
    return render(request, 'cotizaciones/editar_cotizacion.html', {'form': form, 'cotizacion': cotizacion})

@login_required
def eliminar_cotizacion(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    if request.method == 'POST':
        numero = cotizacion.numero
        try:
            cotizacion.delete()
            messages.success(request, f"🗑️ Cotización #{numero} eliminada correctamente.")
        except Exception as e:
            logger.error(f"Error al eliminar cotización {pk}: {str(e)}")
            messages.error(request, "❌ Error al eliminar la cotización.")
        return redirect('cotizaciones:lista')
    return render(request, 'cotizaciones/confirmar_eliminar.html', {'cotizacion': cotizacion})

@login_required
def cambiar_estado_cotizacion(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in dict(Cotizacion.ESTADO_CHOICES):
            cotizacion.estado = nuevo_estado
            cotizacion.save()
            messages.success(request, f"✅ Estado actualizado a '{cotizacion.get_estado_display()}'")
        else:
            messages.error(request, "❌ Estado inválido")
    
    return redirect('cotizaciones:detalle', pk=pk)

def generar_pdf_cotizacion(request, pk, to_buffer=None):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    buffer = to_buffer or BytesIO()
    try:
        doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"Cotización {cotizacion.numero}")
        elements = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1a5490'), spaceAfter=30, alignment=TA_CENTER)
        title = Paragraph(f"COTIZACIÓN #{cotizacion.numero}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        cliente_data = [
            ['INFORMACIÓN DEL CLIENTE', ''],
            ['Nombre:', cotizacion.cliente_nombre],
            ['Razón Social:', cotizacion.razon_social or '-'],
            ['NIT:', cotizacion.nit or '-'],
            ['Dirección:', cotizacion.direccion or '-'],
            ['Teléfono:', cotizacion.telefono],
            ['Email:', cotizacion.correo_electronico],
            ['Fecha:', cotizacion.fecha_creacion.strftime('%d/%m/%Y')],
        ]
        cliente_table = Table(cliente_data, colWidths=[2*inch, 4*inch])
        cliente_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5490')),
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
        for idx, tablero in enumerate(cotizacion.tableros.all(), 1):
            tablero_title = Paragraph(f"<b>ITEM #{idx}</b>", styles['Heading2'])
            elements.append(tablero_title)
            elements.append(Spacer(1, 0.1*inch))
            if tablero.descripcion:
                elements.append(Paragraph(f"<b>Descripción:</b> {tablero.descripcion}", styles['Normal']))
                elements.append(Spacer(1, 0.1*inch))
            tablero_data = [
                ['Valor Tablero', 'Descuento', 'Subtotal'],
                [f'${tablero.valor_tablero:,.0f}', f'{tablero.descuento_tablero}%', f'${tablero.subtotal_tablero_bruto:,.0f}']
            ]
            tablero_table = Table(tablero_data, colWidths=[2*inch, 2*inch, 2*inch])
            tablero_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(tablero_table)
            elements.append(Spacer(1, 0.2*inch))
            if tablero.materiales.exists():
                elements.append(Paragraph("<b>Materiales:</b>", styles['Heading3']))
                materiales_data = [['Material', 'Cantidad', 'Valor Unit.', 'Desc.', 'Subtotal']]
                for material in tablero.materiales.all():
                    materiales_data.append([material.nombre, str(material.cantidad), f'${material.valor_unitario:,.0f}', f'{material.descuento}%', f'${material.subtotal:,.0f}'])
                materiales_data.append(['', '', '', f'Subtotal (desc. {tablero.descuento_materiales}%)', f'${tablero.subtotal_materiales:,.0f}'])
                materiales_table = Table(materiales_data, colWidths=[2*inch, 1*inch, 1.2*inch, 0.8*inch, 1.2*inch])
                materiales_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(materiales_table)
            total_item = Paragraph(f"<b>Total Item #{idx}: ${tablero.subtotal_tablero:,.0f}</b>", ParagraphStyle('ItemTotal', parent=styles['Normal'], fontSize=12, alignment=TA_RIGHT))
            elements.append(total_item)
            elements.append(Spacer(1, 0.3*inch))
        elements.append(Spacer(1, 0.3*inch))
        totales_data = [
            ['TOTALES GENERALES', ''],
            ['Subtotal:', f'${cotizacion.subtotal:,.0f}'],
            ['IVA (19%):', f'${cotizacion.iva:,.0f}'],
            ['TOTAL:', f'${cotizacion.total:,.0f}'],
        ]
        totales_table = Table(totales_data, colWidths=[4*inch, 2*inch])
        totales_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5490')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(totales_table)
        doc.build(elements)
    except Exception as e:
        logger.error(f"Error al generar PDF para cotización {pk}: {str(e)}", exc_info=True)
        raise
    if to_buffer:
        return buffer
    else:
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Cotizacion_{cotizacion.numero}.pdf"'
        return response

@login_required
def enviar_cotizacion_correo(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    if not cotizacion.correo_electronico:
        messages.error(request, "❌ La cotización no tiene un correo electrónico asociado.")
        return redirect("cotizaciones:detalle", pk=pk)
    if not cotizacion.tableros.exists():
        messages.error(request, "❌ La cotización no tiene tableros registrados.")
        return redirect("cotizaciones:detalle", pk=pk)
    try:
        pdf_buffer = BytesIO()
        generar_pdf_cotizacion(request, pk, to_buffer=pdf_buffer)
        pdf_data = pdf_buffer.getvalue()
        if not pdf_data or len(pdf_data) < 1000:
            raise ValueError("Error al generar el PDF")
        asunto = f"Cotización {cotizacion.numero} - SynCroPro"
        mensaje = f"""Hola {cotizacion.cliente_nombre},

Le enviamos su cotización número {cotizacion.numero}.

Total a pagar: ${cotizacion.total:,.0f}

Adjunto encontrará el archivo PDF con los detalles completos.

Atentamente,
El equipo de SynCroPro
"""
        from_email = settings.DEFAULT_FROM_EMAIL
        email = EmailMessage(
            subject=asunto,
            body=mensaje,
            from_email=from_email,
            to=[cotizacion.correo_electronico],
            reply_to=[from_email],
        )
        nombre_archivo = f"Cotizacion_{cotizacion.numero}.pdf"
        email.attach(nombre_archivo, pdf_data, "application/pdf")
        email.send(fail_silently=False)
        logger.info(f"Cotización {cotizacion.numero} enviada exitosamente a {cotizacion.correo_electronico}")
        messages.success(request, f"✅ Cotización enviada exitosamente a {cotizacion.correo_electronico}")
    except Exception as e:
        logger.error(f"Error al enviar cotización {pk}: {str(e)}", exc_info=True)
        messages.error(request, f"❌ Error al enviar el correo: {str(e)}.")
    finally:
        if 'pdf_buffer' in locals():
            pdf_buffer.close()
    return redirect("cotizaciones:detalle", pk=pk)