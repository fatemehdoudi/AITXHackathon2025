from rest_framework import serializers
from .models import InsurancePlan

class InsurancePlanSerializer(serializers.ModelSerializer):
    network_name = serializers.CharField(source="network.name", read_only=True)

    class Meta:
        model = InsurancePlan
        fields = ["id", "network", "network_name", "name", "plan_type", "plan_code", "description"]
