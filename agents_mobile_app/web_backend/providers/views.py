from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter, BooleanFilter, NumberFilter
from .models import Specialty, Provider
from .serializers import SpecialtySerializer, ProviderSerializer

class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all().order_by("name")
    serializer_class = SpecialtySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]

class ProviderFilter(FilterSet):
    city = CharFilter(field_name="city", lookup_expr="iexact")
    state = CharFilter(field_name="state", lookup_expr="iexact")
    specialty = NumberFilter(field_name="specialty_id")
    accepts_new_patients = BooleanFilter(field_name="accepts_new_patients")
    insurance_networks = NumberFilter(field_name="insurance_networks__id")
    insurance_plans = NumberFilter(field_name="insurance_plans__id")
    provider_type = CharFilter(field_name="provider_type", lookup_expr="iexact")

    class Meta:
        model = Provider
        fields = [
            "city", "state", "specialty", "provider_type",
            "accepts_new_patients", "insurance_networks", "insurance_plans",
        ]

class ProviderViewSet(viewsets.ModelViewSet):
    queryset = (
        Provider.objects
        .select_related("specialty")
        .prefetch_related("insurance_networks", "insurance_plans")
        .all()
        .order_by("name")
    )
    serializer_class = ProviderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProviderFilter
    search_fields = ["name", "city", "state", "zip_code", "phone", "website", "address"]
    ordering_fields = ["name", "city", "state", "zip_code", "accepts_new_patients", "id"]
