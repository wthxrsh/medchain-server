import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medchain_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
from sharing.models import AccessRequest

# Find the first patient
patient = User.objects.filter(role='patient').first()
if not patient:
    # If there is no patient with role 'patient', just grab the first user
    patient = User.objects.first()
    if not patient:
        patient = User.objects.create_user(email='testpatient@medchain.com', password='password', first_name='John', last_name='Doe', role='patient')
    else:
        patient.role = 'patient'
        patient.save()

# Indian Doctor Profiles
doctors_data = [
    ("Harpreet", "Singh", "Specialist consultation review"),
    ("Subramaniam", "S.", "Routine lab results sync"),
    ("Ananya", "Sharma", "Cardiology records history"),
    ("Ravi", "Patel", "Physical therapy progress tracking"),
    ("Priya", "Desai", "Post-op surgical review"),
    ("Amit", "Gupta", "Chronic condition monitoring"),
    ("Neha", "Reddy", "Allergy and immunization check"),
    ("Karan", "Malhotra", "Dermatology assessment"),
    ("Aarti", "Iyer", "Neurological exam history"),
    ("Vikram", "Chauhan", "Endocrinology checkup sync"),
    ("Meera", "Joshi", "Orthopedic injury evaluation"),
    ("Rohan", "Mehta", "Annual wellness panel review")
]

# Wipe old test requests and grants to ensure clean slate if needed
# Uncomment if needed

for i, (fn, ln, reason) in enumerate(doctors_data):
    doc_email = f"dr.{fn.lower()}.{ln.lower()}@hospital.com"
    doc, created = User.objects.get_or_create(email=doc_email, defaults={
        'first_name': fn,
        'last_name': ln,
        'role': 'doctor'
    })
    if created:
        doc.set_password('securepassword123')
        doc.save()

    # Distribute statuses nicely
    # Make about 6 pending, 4 approved, 2 declined
    status = 'Pending'
    if i < 4:
        status = 'Approved'
    elif i >= 10:
        status = 'Declined'

    # Ensure no duplicates per doctor to prevent unique constraint issues if running multiple times
    AccessRequest.objects.get_or_create(
        patient=patient,
        doctor=doc,
        defaults={
            'status': status,
            'reason': reason,
        }
    )

print(f"✅ Successfully injected {len(doctors_data)} live access requests into {patient.first_name}'s portal!")
