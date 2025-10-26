from rest_framework import serializers
from .models import Prospect, ContactLog

class ContactLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactLog
        fields = ["id", "method", "outcome", "notes", "contacted_at"]

class ProspectSerializer(serializers.ModelSerializer):
    contacts = ContactLogSerializer(many=True, read_only=True)

    class Meta:
        model = Prospect
        fields = [
            "id", "user", "status", "provider_data",
            "search", "initial_reason", "match_score_snapshot",
            "notes", "next_action_at", "last_contacted_at",
            "created_at", "updated_at", "contacts",
        ]
        read_only_fields = ["created_at", "updated_at", "contacts"]
