import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class Vitals(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vitals', db_index=True)
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    blood_pressure_sys = models.IntegerField(null=True, blank=True, help_text="Systolic (mmHg)")
    blood_pressure_dia = models.IntegerField(null=True, blank=True, help_text="Diastolic (mmHg)")
    heart_rate_bpm = models.IntegerField(null=True, blank=True, help_text="Heart rate (bpm)")
    temperature_c = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text="Temperature (°C)")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Vitals"
        ordering = ['-recorded_at']

    def __str__(self):
        return f"Vitals for {self.user.email} on {self.recorded_at.strftime('%Y-%m-%d')}"


class Diagnosis(models.Model):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Resolved', 'Resolved'),
    )
    SEVERITY_CHOICES = (
        ('Mild', 'Mild'),
        ('Moderate', 'Moderate'),
        ('Severe', 'Severe'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='diagnoses', db_index=True)
    condition_name = models.CharField(max_length=200)
    icd_code = models.CharField(max_length=20, blank=True, help_text="ICD-10 classification code")
    diagnosed_date = models.DateField(db_index=True)
    status = models.CharField(max_length=50, default='Active', choices=STATUS_CHOICES)
    severity = models.CharField(max_length=50, default='Moderate', choices=SEVERITY_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Diagnoses"
        ordering = ['-diagnosed_date']

    def __str__(self):
        return f"Diagnosis: {self.condition_name} ({self.icd_code}) for {self.user.email}"


class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prescriptions', db_index=True)
    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100, help_text="e.g., 500mg")
    frequency = models.CharField(max_length=100, help_text="e.g., Once daily")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    refills_remaining = models.IntegerField(default=0)
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"Prescription: {self.medication_name} ({self.dosage}) for {self.user.email}"
