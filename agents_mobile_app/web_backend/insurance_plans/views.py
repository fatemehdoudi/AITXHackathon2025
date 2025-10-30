from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import InsurancePlan
from .serializers import InsurancePlanSerializer

class InsurancePlanViewSet(viewsets.ModelViewSet):
    queryset = InsurancePlan.objects.select_related("network").all().order_by("network__name", "name")
    serializer_class = InsurancePlanSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["network", "plan_type"]
    search_fields = ["name", "plan_code", "network__name"]
    ordering_fields = ["name", "plan_type", "plan_code"]
