"""
Management command to enter Rylen Reed's vaccine dates from his paper immunization record.

Place this file at:
  students/management/commands/update_rylen_vaccine_dates.py

Run with:
  python manage.py update_rylen_vaccine_dates

Use --dry-run to preview without saving:
  python manage.py update_rylen_vaccine_dates --dry-run
"""

from datetime import date
from django.core.management.base import BaseCommand
from students.models import Student, Immunization, VaccineDose, VaccineType


# ── Rylen Reed's dates read directly from the paper record ────────────────────
# Format: { 'VACCINE_NAME': { dose_number: date(YYYY, MM, DD), ... }, ... }
# Vaccine names must match VaccineType.name exactly (case-sensitive).
RYLEN_DOSES = {
    'COVID-19': {
        1: date(2022, 1, 19),
        2: date(2022, 2,  9),
    },
    'DTaP': {
        1: date(2017, 4, 21),
        2: date(2017, 10,  5),
        3: date(2018, 1, 23),
        4: date(2021, 8,  2),
        # Dose 5 — not on the paper record; leave untouched
    },
    'HEP A': {
        1: date(2018, 1, 23),
        2: date(2018, 8,  2),
    },
    'HEP B': {
        1: date(2017, 4, 21),
        2: date(2017, 10,  5),
        3: date(2017, 12,  5),
        4: date(2018, 1, 23),
        5: date(2021, 8,  2),
    },
    'HIB': {
        1: date(2017, 4, 21),
        2: date(2017, 10,  5),
        3: date(2018, 1, 23),
        4: date(2021, 8,  2),
    },
    'IPV': {
        1: date(2017, 4, 21),
        2: date(2017, 10,  5),
        3: date(2018, 1, 23),
        4: date(2021, 8,  2),
    },
    'Influenza': {
        1: date(2022, 1, 14),
        2: date(2022, 1, 23),
    },
    'MMR': {
        1: date(2018, 1, 23),
        2: date(2021, 8,  2),
    },
    'MMRV': {
        1: date(2021, 1, 23),
        2: date(2021, 8,  2),
    },
    'PCV-13': {
        1: date(2017, 4, 21),
        2: date(2017, 10,  5),
        3: date(2018, 1, 23),
        4: date(2021, 8,  2),
    },
    'VARICELLA': {
        1: date(2018, 1, 23),
        2: date(2021, 8,  2),
    },
}


class Command(BaseCommand):
    help = "Enter Rylen Reed's vaccine dates from his paper immunization record."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving anything to the database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        # ── Find Rylen Reed ───────────────────────────────────────────────────
        try:
            student = Student.objects.get(
                first_name__iexact='Rylen',
                last_name__iexact='Reed',
            )
        except Student.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                '❌  Student "Rylen Reed" not found. '
                'Check the spelling in the database.'
            ))
            return
        except Student.MultipleObjectsReturned:
            self.stdout.write(self.style.ERROR(
                '❌  Multiple students named "Rylen Reed" found. '
                'Run this manually after identifying the correct pk.'
            ))
            return

        self.stdout.write(
            f'Found student: {student.get_full_name()} '
            f'(DOB: {student.date_of_birth}, pk={student.pk})\n'
        )

        # ── Get or create the immunization record ─────────────────────────────
        immunization, created = Immunization.objects.get_or_create(student=student)
        if created:
            self.stdout.write('  Created new Immunization record.\n')

        # ── Apply dates ───────────────────────────────────────────────────────
        updated = 0
        skipped = 0
        not_found = 0

        for vaccine_name, doses in RYLEN_DOSES.items():
            # Look up the VaccineType
            try:
                vaccine_type = VaccineType.objects.get(name=vaccine_name)
            except VaccineType.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'  ⚠  VaccineType "{vaccine_name}" not found — skipping.'
                ))
                not_found += len(doses)
                continue

            for dose_number, admin_date in doses.items():
                try:
                    dose = VaccineDose.objects.get(
                        immunization=immunization,
                        vaccine_type=vaccine_type,
                        dose_schedule__dose_number=dose_number,
                    )
                except VaccineDose.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠  {vaccine_name} Dose {dose_number} row not found — skipping. '
                        f'Run backfill_vaccine_doses first.'
                    ))
                    not_found += 1
                    continue

                # Already has a date — report and skip to avoid overwriting
                if dose.date_administered:
                    self.stdout.write(
                        f'  —  {vaccine_name} Dose {dose_number}: '
                        f'already has date {dose.date_administered}, skipping.'
                    )
                    skipped += 1
                    continue

                self.stdout.write(
                    f'  ✅  {vaccine_name} Dose {dose_number}: '
                    f'setting date → {admin_date}'
                )

                if not dry_run:
                    dose.date_administered = admin_date
                    dose.save(update_fields=['date_administered', 'updated_at'])

                updated += 1

        # ── Summary ───────────────────────────────────────────────────────────
        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN complete. '
                f'{updated} dose(s) would be updated, '
                f'{skipped} already had dates, '
                f'{not_found} rows not found.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Done. {updated} dose(s) updated, '
                f'{skipped} already had dates (left untouched), '
                f'{not_found} rows not found.'
            ))