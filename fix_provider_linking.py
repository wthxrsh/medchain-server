"""
Fix script:
1. Normalize all role strings to uppercase (DOCTOR, PATIENT)
2. Backfill doctor FK on all existing appointments via name matching
3. Create AccessGrant between rocky1234 and laukikparashare
"""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medchain_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# ── Step 1: Normalize roles ────────────────────────────────────────────────
u1 = User.objects.filter(role='doctor').update(role='DOCTOR')
u2 = User.objects.filter(role='patient').update(role='PATIENT')
print(f"Normalized roles: {u1} doctor -> DOCTOR, {u2} patient -> PATIENT")

# ── Step 2: Backfill appointment doctor FK ─────────────────────────────────
from appointments.models import Appointment

fixed = 0
for apt in Appointment.objects.filter(doctor__isnull=True):
    raw = apt.doctor_name
    clean = raw.replace('Dr. ', '').replace('Dr.', '').strip()
    parts = clean.split(' ')
    doctor = None

    if len(parts) >= 2:
        first = parts[0]
        last = ' '.join(parts[1:])
        doctor = User.objects.filter(role='DOCTOR', first_name__iexact=first, last_name__iexact=last).first()

    if not doctor and parts:
        # Try partial first name match
        doctor = User.objects.filter(role='DOCTOR', first_name__icontains=parts[0]).first()

    if not doctor:
        # Try partial last name match
        doctor = User.objects.filter(role='DOCTOR', last_name__icontains=parts[-1]).first()

    if doctor:
        apt.doctor = doctor
        apt.save(update_fields=['doctor'])
        fixed += 1
        print(f"  Linked: '{raw}' -> {doctor.email}")
    else:
        print(f"  No match: '{raw}'")

print(f"\nFixed {fixed} appointment doctor FKs")

# ── Step 3: Show AccessGrants summary ─────────────────────────────────────
from sharing.models import AccessGrant, AccessRequest

rocky = User.objects.filter(email='rocky1234@gmail.com').first()
laukik = User.objects.filter(email='laukikparashare@gmail.com').first()

print(f"\nrocky1234 user: {rocky}")
print(f"laukikparashare user: {laukik}")

if rocky and laukik:
    grant, created = AccessGrant.objects.get_or_create(doctor=rocky, patient=laukik)
    print(f"AccessGrant rocky->laukik: {'CREATED' if created else 'already existed'}")
    
    # Also create/update access request so it appears in patient requests
    req, created2 = AccessRequest.objects.get_or_create(
        doctor=rocky, 
        patient=laukik,
        defaults={'reason': 'Provider access', 'status': 'Approved'}
    )
    if not created2 and req.status != 'Approved':
        req.status = 'Approved'
        req.save()
        print("AccessRequest rocky->laukik: Updated to Approved")
    else:
        print(f"AccessRequest rocky->laukik: {'CREATED' if created2 else 'already existed'}")

# ── Step 4: Final verification ─────────────────────────────────────────────
print("\n=== FINAL APPOINTMENT STATE ===")
for a in Appointment.objects.all():
    print(f"  {a.doctor_name} | FK={a.doctor.email if a.doctor else 'NONE'} | patient={a.user.email} | status={a.status}")

print("\n=== GRANTS for rocky1234 ===")
for g in AccessGrant.objects.filter(doctor=rocky):
    print(f"  patient={g.patient.email}")

print("\nDone!")
