from rest_framework.views import APIView
from rest_framework.response import Response
from cotizaciones.models import Cotizacion
from cotizaciones.serializers import CotizacionSerializer

class CotizacionesAprobadasAPI(APIView):
    def get(self, request):
        cotizaciones = Cotizacion.objects.filter(estado='aprobada')
        serializer = CotizacionSerializer(cotizaciones, many=True)
        return Response(serializer.data)