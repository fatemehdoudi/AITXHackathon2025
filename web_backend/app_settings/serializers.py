from rest_framework import serializers
from .models import UserSettings

class UserSettingsSerializer(serializers.ModelSerializer):
    insurance_network_name = serializers.CharField(source="insurance_network.name", read_only=True)
    insurance_plan_name = serializers.CharField(source="insurance_plan.name", read_only=True)

    class Meta:
        model = UserSettings
        fields = [
            "id", "user", "age",
            "insurance_network", "insurance_network_name",
            "insurance_plan", "insurance_plan_name",
            "default_radius_miles",
            "created_at", "updated_at", "group_id", "member_id", "member_first_name", "member_last_name",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_age(self, v):
        if v is not None and (v < 0 or v > 120):
            raise serializers.ValidationError("Age must be between 0 and 120.")
        return v

    def validate_default_radius_miles(self, v):
        if v < 1 or v > 200:
            raise serializers.ValidationError("Radius must be between 1 and 200 miles.")
        return v
