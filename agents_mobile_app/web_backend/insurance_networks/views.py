from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import InsuranceNetwork
from .serializers import InsuranceNetworkSerializer

class InsuranceNetworkViewSet(viewsets.ModelViewSet):
    queryset = InsuranceNetwork.objects.all().order_by("name")
    serializer_class = InsuranceNetworkSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]
