from django.db import models

class InsuranceNetwork(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # umbrella brand for grouping (helps show “BCBS” rollups)
    brand = models.CharField(
        max_length=80,
        blank=True,
        help_text="Top-level brand, e.g., 'Blue Cross Blue Shield', 'Aetna', 'UnitedHealthcare'."
    )

    # region served; keep simple for hackathon (comma-separated states/regions)
    service_area = models.CharField(
        max_length=200,
        blank=True,
        help_text="Comma-separated regions/states, e.g., 'TX' or 'MD,DC,VA'."
    )
    description = models.TextField(blank=True)
    website = models.URLField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name


class InsuranceAlias(models.Model):
    """
    Lets user input like 'BCBS Texas' or just 'BCBS' map to the real company.
    """
    alias = models.CharField(max_length=150, unique=True)
    network = models.ForeignKey(InsuranceNetwork, on_delete=models.CASCADE, related_name="aliases")

    def __str__(self):
        return f"{self.alias} → {self.network.name}"