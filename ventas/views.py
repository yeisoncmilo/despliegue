from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.conf import settings
from django.core.mail import EmailMessage
from io import BytesIO
import logging
from .models import Venta, VentaTablero, VentaMaterial
from .forms import VentaForm
from cotizaciones.models import Cotizacion

logger = logging.getLogger(__name__)

@login_required
def lista_ventas(request):
    ventas = Venta.objects.all().order_by('-fecha_venta')
    return render(request, 'ventas/lista_ventas.html', {'ventas': ventas})

def generar_numero_venta():
    return Venta.generar_numero()

def procesar_tableros_materiales_venta(venta, post_data):
    venta.tableros_venta.all().delete()
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
        tablero = VentaTablero.objects.create(
            venta=venta,
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
            VentaMaterial.objects.create(
                venta_tablero=tablero,
                nombre=nombre,
                cantidad=cantidad,
                valor_unitario=valor_unitario,
                descuento=descuento
            )

@login_required
def crear_venta(request, cotizacion_pk=None):
    numero_generado = generar_numero_venta()
    cotizacion_origen = None
    
    if cotizacion_pk:
        cotizacion_origen = get_object_or_404(Cotizacion, pk=cotizacion_pk, estado='aprobada')
    
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    venta = form.save(commit=False)
                    venta.numero = numero_generado
                    
                    if cotizacion_origen:
                        venta.cotizacion = cotizacion_origen
                        venta.cliente_nombre = cotizacion_origen.cliente_nombre
                        venta.razon_social = cotizacion_origen.razon_social
                        venta.nit = cotizacion_origen.nit
                        venta.direccion = cotizacion_origen.direccion
                        venta.telefono = cotizacion_origen.telefono
                        venta.correo_electronico = cotizacion_origen.correo_electronico
                    
                    venta.save()
                    procesar_tableros_materiales_venta(venta, request.POST)
                    
                    if cotizacion_origen:
                        messages.success(request, f"✅ Venta #{venta.numero} creada exitosamente desde cotización.")
                    else:
                        messages.success(request, f"✅ Venta #{venta.numero} creada exitosamente.")
                    
                    return redirect('ventas:detalle', pk=venta.pk)
            except Exception as e:
                logger.error(f"Error al crear venta: {str(e)}", exc_info=True)
                messages.error(request, f"❌ Error al guardar la venta: {str(e)}")
        else:
            messages.error(request, "❌ Por favor, corrige los errores en el formulario.")
    else:
        initial_data = {}
        if cotizacion_origen:
            initial_data = {
                'cliente_nombre': cotizacion_origen.cliente_nombre,
                'razon_social': cotizacion_origen.razon_social,
                'nit': cotizacion_origen.nit,
                'direccion': cotizacion_origen.direccion,
                'telefono': cotizacion_origen.telefono,
                'correo_electronico': cotizacion_origen.correo_electronico,
            }
        form = VentaForm(initial=initial_data)
    
    # Obtener cotizaciones aprobadas para el select
    cotizaciones = Cotizacion.objects.filter(estado='aprobada').order_by('-fecha_creacion')
    
    context = {
        'form': form, 
        'numero_generado': numero_generado,
        'cotizacion_origen': cotizacion_origen,
        'cotizaciones': cotizaciones  # ✅ ESTA LÍNEA ES CLAVE
    }
    return render(request, 'ventas/nueva_venta.html', context)

@login_required
def detalle_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    tableros = venta.tableros_venta.all()
    return render(request, 'ventas/detalle_venta.html', {
        'venta': venta,
        'tableros': tableros,
        'subtotal': venta.subtotal,
        'iva': venta.iva,
        'total': venta.total,
    })

@login_required
def editar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    
    if venta.estado == 'pagada':
        messages.error(request, "❌ No se puede editar una venta pagada.")
        return redirect('ventas:detalle', pk=venta.pk)
    
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=venta)
        if form.is_valid():
            try:
                with transaction.atomic():
                    venta = form.save()
                    procesar_tableros_materiales_venta(venta, request.POST)
                    messages.success(request, f"✅ Venta #{venta.numero} actualizada correctamente.")
                    return redirect('ventas:detalle', pk=venta.pk)
            except Exception as e:
                logger.error(f"Error al editar venta {pk}: {str(e)}", exc_info=True)
                messages.error(request, f"❌ Error al actualizar la venta: {str(e)}")
        else:
            messages.error(request, "❌ Corrige los errores antes de guardar.")
    else:
        form = VentaForm(instance=venta)
    
    return render(request, 'ventas/editar_venta.html', {
        'form': form, 
        'venta': venta,
        'tableros': venta.tableros_venta.all()
    })

@login_required
def eliminar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        numero = venta.numero
        try:
            venta.estado = 'anulada'
            venta.save()
            messages.success(request, f"🗑️ Venta #{numero} anulada correctamente.")
        except Exception as e:
            logger.error(f"Error al anular venta {pk}: {str(e)}")
            messages.error(request, "❌ Error al anular la venta.")
        return redirect('ventas:lista')
    return render(request, 'ventas/eliminar_ventas.html', {'venta': venta})

def generar_pdf_venta(request, pk, to_buffer=None):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    venta = get_object_or_404(Venta, pk=pk)
    buffer = to_buffer or BytesIO()
    try:
        doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"Venta {venta.numero}")
        elements = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, 
                                   textColor=colors.HexColor('#28a745'), spaceAfter=30, alignment=TA_CENTER)
        title = Paragraph(f"FACTURA DE VENTA #{venta.numero}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        cliente_data = [
            ['INFORMACIÓN DEL CLIENTE', ''],
            ['Nombre:', venta.cliente_nombre],
            ['Razón Social:', venta.razon_social or '-'],
            ['NIT:', venta.nit or '-'],
            ['Dirección:', venta.direccion or '-'],
            ['Teléfono:', venta.telefono],
            ['Email:', venta.correo_electronico],
            ['Fecha Venta:', venta.fecha_venta.strftime('%d/%m/%Y')],
            ['Método Pago:', venta.get_metodo_pago_display()],
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
        
        for idx, tablero in enumerate(venta.tableros_venta.all(), 1):
            tablero_title = Paragraph(f"<b>ITEM #{idx}</b>", styles['Heading2'])
            elements.append(tablero_title)
            elements.append(Spacer(1, 0.1*inch))
            if tablero.descripcion:
                elements.append(Paragraph(f"<b>Descripción:</b> {tablero.descripcion}", styles['Normal']))
                elements.append(Spacer(1, 0.1*inch))
            tablero_data = [
                ['Valor Item', 'Descuento', 'Subtotal'],
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
            
            if tablero.materiales_venta.exists():
                elements.append(Paragraph("<b>Materiales:</b>", styles['Heading3']))
                materiales_data = [['Material', 'Cantidad', 'Valor Unit.', 'Desc.', 'Subtotal']]
                for material in tablero.materiales_venta.all():
                    materiales_data.append([material.nombre, str(material.cantidad), 
                                          f'${material.valor_unitario:,.0f}', f'{material.descuento}%', 
                                          f'${material.subtotal:,.0f}'])
                materiales_data.append(['', '', '', f'Subtotal (desc. {tablero.descuento_materiales}%)', 
                                      f'${tablero.subtotal_materiales:,.0f}'])
                materiales_table = Table(materiales_data, colWidths=[2*inch, 1*inch, 1.2*inch, 0.8*inch, 1.2*inch])
                materiales_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(materiales_table)
            
            total_item = Paragraph(f"<b>Total Item #{idx}: ${tablero.subtotal_tablero:,.0f}</b>", 
                                 ParagraphStyle('ItemTotal', parent=styles['Normal'], fontSize=12, alignment=TA_RIGHT))
            elements.append(total_item)
            elements.append(Spacer(1, 0.3*inch))
        
        elements.append(Spacer(1, 0.3*inch))
        totales_data = [
            ['TOTALES FACTURA', ''],
            ['Subtotal:', f'${venta.subtotal:,.0f}'],
            ['IVA (19%):', f'${venta.iva:,.0f}'],
            ['TOTAL A PAGAR:', f'${venta.total:,.0f}'],
            ['Estado:', venta.get_estado_display().upper()],
        ]
        totales_table = Table(totales_data, colWidths=[4*inch, 2*inch])
        totales_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(totales_table)
        doc.build(elements)
    except Exception as e:
        logger.error(f"Error al generar PDF para venta {pk}: {str(e)}", exc_info=True)
        raise
    if to_buffer:
        return buffer
    else:
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Factura_{venta.numero}.pdf"'
        return response

@login_required
def enviar_venta_correo(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if not venta.correo_electronico:
        messages.error(request, "❌ La venta no tiene un correo electrónico asociado.")
        return redirect("ventas:detalle", pk=pk)
    if not venta.tableros_venta.exists():
        messages.error(request, "❌ La venta no tiene items registrados.")
        return redirect("ventas:detalle", pk=pk)
    try:
        pdf_buffer = BytesIO()
        generar_pdf_venta(request, pk, to_buffer=pdf_buffer)
        pdf_data = pdf_buffer.getvalue()
        if not pdf_data or len(pdf_data) < 1000:
            raise ValueError("Error al generar el PDF")
        asunto = f"Factura Venta {venta.numero} - SynCroPro"
        mensaje = f"""Hola {venta.cliente_nombre},

Le enviamos la factura de su compra número {venta.numero}.

Total: ${venta.total:,.0f}
Método de Pago: {venta.get_metodo_pago_display()}
Estado: {venta.get_estado_display()}

Adjunto encontrará el archivo PDF con los detalles completos.

Atentamente,
El equipo de SynCroPro
"""
        from_email = settings.DEFAULT_FROM_EMAIL
        email = EmailMessage(
            subject=asunto,
            body=mensaje,
            from_email=from_email,
            to=[venta.correo_electronico],
            reply_to=[from_email],
        )
        nombre_archivo = f"Factura_{venta.numero}.pdf"
        email.attach(nombre_archivo, pdf_data, "application/pdf")
        email.send(fail_silently=False)
        logger.info(f"Venta {venta.numero} enviada exitosamente a {venta.correo_electronico}")
        messages.success(request, f"✅ Factura enviada exitosamente a {venta.correo_electronico}")
    except Exception as e:
        logger.error(f"Error al enviar venta {pk}: {str(e)}", exc_info=True)
        messages.error(request, f"❌ Error al enviar el correo: {str(e)}.")
    finally:
        if 'pdf_buffer' in locals():
            pdf_buffer.close()
    return redirect("ventas:detalle", pk=pk)

@login_required
def convertir_cotizacion_a_venta(request, cotizacion_pk):
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_pk)
    
    if cotizacion.estado != 'aprobada':
        messages.error(request, "❌ Solo se pueden convertir cotizaciones aprobadas a ventas.")
        return redirect('cotizaciones:detalle', pk=cotizacion_pk)
    
    if hasattr(cotizacion, 'venta'):
        messages.warning(request, "⚠️ Esta cotización ya tiene una venta asociada.")
        return redirect('ventas:detalle', pk=cotizacion.venta.pk)
    
    return redirect('ventas:crear', cotizacion_pk=cotizacion_pk)

# **VISTA AJAX PARA CARGAR COTIZACIÓN**
@login_required
def cargar_cotizacion(request, pk):
    """Vista AJAX para cargar datos de cotización en el formulario de ventas"""
    try:
        cotizacion = get_object_or_404(Cotizacion, pk=pk)
        
        # Construir lista de tableros con sus materiales
        tableros_data = []
        for tablero in cotizacion.tableros.all():
            materiales_data = []
            for material in tablero.materiales.all():
                materiales_data.append({
                    'nombre': material.nombre,
                    'cantidad': material.cantidad,
                    'valor_unitario': material.valor_unitario,
                    'descuento': material.descuento
                })
            
            tableros_data.append({
                'descripcion': tablero.descripcion,
                'valor_tablero': tablero.valor_tablero,
                'descuento_tablero': tablero.descuento_tablero,
                'descuento_materiales': tablero.descuento_materiales,
                'materiales': materiales_data
            })
        
        return JsonResponse({
            'cliente_nombre': cotizacion.cliente_nombre,
            'razon_social': cotizacion.razon_social or '',
            'nit': cotizacion.nit or '',
            'direccion': cotizacion.direccion or '',
            'telefono': cotizacion.telefono,
            'correo_electronico': cotizacion.correo_electronico,
            'tableros': tableros_data
        })
    except Exception as e:
        logger.error(f"Error en AJAX cargar cotización: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)