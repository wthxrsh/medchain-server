from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from clinical.models import Vitals, Diagnosis, Prescription

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds clinical data (vitals, diagnoses, and prescriptions) for testing'

    def handle(self, *args, **options):
        email = "laukikparashare@gmail.com"
        try:
            patient = User.objects.get(email=email)
            self.stdout.write(self.style.SUCCESS(f"Found patient user: {patient.email}"))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Patient user '{email}' does not exist! Please register them first."))
            return

        # ── Clear existing clinical data for this user to ensure idempotency ──
        Vitals.objects.filter(user=patient).delete()
        Diagnosis.objects.filter(user=patient).delete()
        Prescription.objects.filter(user=patient).delete()
        self.stdout.write(self.style.WARNING("Cleared existing clinical data for clean seeding..."))

        # ── Seed Vitals ──
        vitals_data = [
            Vitals(
                user=patient,
                recorded_at=timezone.now() - timedelta(days=60),
                weight_kg=72.5,
                height_cm=175.0,
                blood_pressure_sys=135,
                blood_pressure_dia=85,
                heart_rate_bpm=78,
                temperature_c=36.8,
                notes="Patient reported mild recurring headache. Blood pressure slightly elevated. Overall stable."
            ),
            Vitals(
                user=patient,
                recorded_at=timezone.now() - timedelta(days=30),
                weight_kg=71.8,
                height_cm=175.0,
                blood_pressure_sys=128,
                blood_pressure_dia=82,
                heart_rate_bpm=72,
                temperature_c=36.6,
                notes="Follow-up check. Blood pressure stabilizing. Patient started a low sodium diet. Weight slightly decreased."
            ),
            Vitals(
                user=patient,
                recorded_at=timezone.now() - timedelta(days=7),
                weight_kg=71.2,
                height_cm=175.0,
                blood_pressure_sys=122,
                blood_pressure_dia=80,
                heart_rate_bpm=70,
                temperature_c=36.7,
                notes="Vitals normal. Blood pressure well controlled under current medication regimen."
            ),
        ]
        Vitals.objects.bulk_create(vitals_data)
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded 3 vitals records."))

        # ── Seed Diagnoses ──
        diagnoses_data = [
            Diagnosis(
                user=patient,
                condition_name="Mild Hypertension",
                icd_code="I10",
                diagnosed_date=date.today() - timedelta(days=60),
                status="Active",
                severity="Mild",
                notes="Diagnosed after two consecutive elevated blood pressure readings at the clinic. Family history of cardiovascular disease noted."
            ),
            Diagnosis(
                user=patient,
                condition_name="Seasonal Allergies",
                icd_code="J30.9",
                diagnosed_date=date.today() - timedelta(days=45),
                status="Resolved",
                severity="Mild",
                notes="Acute rhinitis caused by spring pollen. Successfully resolved with 2 weeks of antihistamines."
            ),
        ]
        Diagnosis.objects.bulk_create(diagnoses_data)
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded 2 diagnosis records."))

        # ── Seed Prescriptions ──
        prescriptions_data = [
            Prescription(
                user=patient,
                medication_name="Lisinopril 10mg",
                dosage="10mg",
                frequency="Once daily in the morning",
                start_date=date.today() - timedelta(days=60),
                end_date=date.today() + timedelta(days=120),
                refills_remaining=5,
                instructions="Take with a full glass of water. Monitor for dry cough. Avoid potassium supplements unless advised."
            ),
            Prescription(
                user=patient,
                medication_name="Loratadine 10mg",
                dosage="10mg",
                frequency="Once daily at night as needed",
                start_date=date.today() - timedelta(days=45),
                end_date=date.today() - timedelta(days=31),
                refills_remaining=0,
                instructions="Take with or without food. May cause mild drowsiness. Do not consume alcohol concurrently."
            ),
        ]
        Prescription.objects.bulk_create(prescriptions_data)
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded 2 prescription records."))
        self.stdout.write(self.style.SUCCESS("All clinical seed data successfully inserted!"))
