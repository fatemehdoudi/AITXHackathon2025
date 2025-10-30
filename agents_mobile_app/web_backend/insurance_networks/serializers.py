from rest_framework import serializers
from .models import InsuranceNetwork

class InsuranceNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceNetwork
        fields = ["id", "name", "description", "website", "phone_number"]
