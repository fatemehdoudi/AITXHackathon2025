from rest_framework import serializers
from .models import Specialty, Provider

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ["id", "name"]

class ProviderSerializer(serializers.ModelSerializer):
    specialty_name = serializers.CharField(source="specialty.name", read_only=True)
    insurance_networks = serializers.PrimaryKeyRelatedField(many=True, read_only=False, required=False, queryset=Provider.insurance_networks.field.remote_field.model.objects.all())
    # Only include plans if you created the insurance_plans app
    from insurance_plans.models import InsurancePlan
    insurance_plans = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=InsurancePlan.objects.all())

    class Meta:
        model = Provider
        fields = [
            "id", "name", "provider_type", "specialty", "specialty_name",
            "address", "city", "state", "zip_code", "phone", "website",
            "accepts_new_patients", "insurance_networks", "insurance_plans",
            "latitude", "longitude",
        ]
