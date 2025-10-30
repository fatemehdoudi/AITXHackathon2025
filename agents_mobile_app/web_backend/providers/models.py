from django.db import models
from insurance_networks.models import InsuranceNetwork
from insurance_plans.models import InsurancePlan

class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Provider(models.Model):
    PROVIDER_TYPES = [
        ('doctor', 'Doctor'),
        ('hospital', 'Hospital'),
        ('clinic', 'Clinic'),
        ('telehealth', 'Telehealth Service'),
    ]

    name = models.CharField(max_length=255)
    provider_type = models.CharField(max_length=50, choices=PROVIDER_TYPES)
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    medmatch_score = models.IntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True, null=True)
    accepts_new_patients = models.BooleanField(default=True)

    # Relations
    insurance_networks = models.ManyToManyField(
        'insurance_networks.InsuranceNetwork',
        related_name='providers',
        blank=True
    )
    insurance_plans = models.ManyToManyField(
        InsurancePlan,
        related_name='providers',
        blank=True
    )
    # Optional metadata (helpful for Nemotron/Tavily)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"
