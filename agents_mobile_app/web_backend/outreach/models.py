from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Prospect(models.Model):
    class Status(models.TextChoices):
        SAVED = "SAVED", "Saved"
        CONTACTED = "CONTACTED", "Contacted"
        APPT_SET = "APPT_SET", "Appt Set"
        NOT_INTERESTED = "NOT_INTERESTED", "Not Interested"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="prospects")
    # provider_data = models.JSONField()  # Storing provider data as JSON
    provider_data = models.JSONField(default=dict, blank=True)  # <— add default
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SAVED)
    # Optional context
    search = models.ForeignKey("searches.UserSearch", null=True, blank=True, on_delete=models.SET_NULL, related_name="prospects")
    initial_reason = models.TextField(blank=True, help_text="Why this provider was saved (e.g., from LLM summary).")
    match_score_snapshot = models.FloatField(null=True, blank=True)
    # User notes & reminders
    notes = models.TextField(blank=True)
    next_action_at = models.DateTimeField(null=True, blank=True)
    last_contacted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # class Meta:
        # unique_together = [("user")]  # one prospect per user/provider

    # def __str__(self):
    #     return f"{self.user_id} → ({self.status})"


class ContactLog(models.Model):
    class Method(models.TextChoices):
        PHONE = "PHONE", "Phone"
        EMAIL = "EMAIL", "Email"
        WEBFORM = "WEBFORM", "Web Form"
        OTHER = "OTHER", "Other"

    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, related_name="contacts")
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.OTHER)
    outcome = models.CharField(max_length=100, blank=True, help_text="e.g., Left VM, Spoke to front desk, Emailed")
    notes = models.TextField(blank=True)
    contacted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contact {self.id} for Prospect {self.prospect_id}"
