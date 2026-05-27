"""
Data Migration: Seed standard CDC vaccine types and dose schedules
Run with: python manage.py migrate students

Place this file at:
  students/migrations/0003_seed_vaccine_types.py
"""

from django.db import migrations


VACCINES = [
    # (name, full_name, total_doses, doses_list)
    # doses_list = [(dose_number, cdc_text, recommended_age_months)]
    (
        "COVID-19",
        "COVID-19 Vaccine",
        2,
        [
            (1, "Dose 1 — Primary series",         2),   # 6 months+
            (2, "Dose 2 — Primary series",         4),
        ]
    ),
    (
        "DTaP",
        "Diphtheria, Tetanus & Pertussis (DTaP)",
        5,
        [
            (1, "Dose 1 — 2 months",     2),
            (2, "Dose 2 — 4 months",     4),
            (3, "Dose 3 — 6 months",     6),
            (4, "Dose 4 — 15–18 months", 15),
            (5, "Dose 5 — 4–6 years",    48),
        ]
    ),
    (
        "HEP A",
        "Hepatitis A Vaccine",
        2,
        [
            (1, "Dose 1 — 12–23 months", 12),
            (2, "Dose 2 — 6–18 months after dose 1", 18),
        ]
    ),
    (
        "HEP B",
        "Hepatitis B Vaccine",
        3,
        [
            (1, "Dose 1 — Birth",        0),
            (2, "Dose 2 — 1–2 months",   1),
            (3, "Dose 3 — 6–18 months",  6),
        ]
    ),
    (
        "HIB",
        "Haemophilus influenzae type b (Hib)",
        4,
        [
            (1, "Dose 1 — 2 months",     2),
            (2, "Dose 2 — 4 months",     4),
            (3, "Dose 3 — 6 months",     6),
            (4, "Dose 4 — 12–15 months", 12),
        ]
    ),
    (
        "IPV",
        "Inactivated Poliovirus Vaccine (IPV)",
        4,
        [
            (1, "Dose 1 — 2 months",     2),
            (2, "Dose 2 — 4 months",     4),
            (3, "Dose 3 — 6–18 months",  6),
            (4, "Dose 4 — 4–6 years",    48),
        ]
    ),
    (
        "Influenza",
        "Influenza (Flu) Vaccine",
        2,
        [
            (1, "Dose 1 — First season (6 months+)", 6),
            (2, "Dose 2 — Second dose same season (if first time)", 7),
        ]
    ),
    (
        "MMR",
        "Measles, Mumps & Rubella (MMR)",
        2,
        [
            (1, "Dose 1 — 12–15 months", 12),
            (2, "Dose 2 — 4–6 years",    48),
        ]
    ),
    (
        "MMRV",
        "Measles, Mumps, Rubella & Varicella (MMRV)",
        2,
        [
            (1, "Dose 1 — 12–15 months", 12),
            (2, "Dose 2 — 4–6 years",    48),
        ]
    ),
    (
        "PCV-13",
        "Pneumococcal Conjugate Vaccine (PCV13)",
        4,
        [
            (1, "Dose 1 — 2 months",     2),
            (2, "Dose 2 — 4 months",     4),
            (3, "Dose 3 — 6 months",     6),
            (4, "Dose 4 — 12–15 months", 12),
        ]
    ),
    (
        "VARICELLA",
        "Varicella (Chickenpox) Vaccine",
        2,
        [
            (1, "Dose 1 — 12–15 months", 12),
            (2, "Dose 2 — 4–6 years",    48),
        ]
    ),
]


def seed_vaccines(apps, schema_editor):
    VaccineType         = apps.get_model('students', 'VaccineType')
    VaccineDoseSchedule = apps.get_model('students', 'VaccineDoseSchedule')

    for order, (name, full_name, total_doses, doses) in enumerate(VACCINES, start=1):
        vt, created = VaccineType.objects.get_or_create(
            name=name,
            defaults={
                'full_name':     full_name,
                'total_doses':   total_doses,
                'is_active':     True,
                'display_order': order,
            }
        )
        # If it already exists but was created without a full_name, update it
        if not created and not vt.full_name:
            vt.full_name = full_name
            vt.display_order = order
            vt.save()

        for dose_num, cdc_text, age_months in doses:
            VaccineDoseSchedule.objects.get_or_create(
                vaccine_type=vt,
                dose_number=dose_num,
                defaults={
                    'cdc_recommendation_text': cdc_text,
                    'recommended_age_months':  age_months,
                    'is_catch_up':             False,
                }
            )


def unseed_vaccines(apps, schema_editor):
    """Reverse: remove only the vaccines we seeded (by name)."""
    VaccineType = apps.get_model('students', 'VaccineType')
    names = [v[0] for v in VACCINES]
    VaccineType.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0002_vaccinetype_student_additional_details_and_more'),  # ← FIXED
    ]

    operations = [
        migrations.RunPython(seed_vaccines, reverse_code=unseed_vaccines),
    ]