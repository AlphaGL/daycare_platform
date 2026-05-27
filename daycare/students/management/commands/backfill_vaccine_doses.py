"""
Management command to backfill vaccine doses for all existing students.

Place this file at:
  students/management/commands/backfill_vaccine_doses.py

Make sure the directory structure exists:
  students/
    management/
      __init__.py
      commands/
        __init__.py
        backfill_vaccine_doses.py

Run with:
  python manage.py backfill_vaccine_doses
"""

from django.core.management.base import BaseCommand
from students.models import Student, Immunization, VaccineType, VaccineDose


class Command(BaseCommand):
    help = 'Backfill vaccine dose rows for all existing students based on active VaccineTypes'

    def handle(self, *args, **options):
        vaccine_types = VaccineType.objects.filter(is_active=True).prefetch_related('dose_schedules')

        if not vaccine_types.exists():
            self.stdout.write(self.style.ERROR(
                '❌  No active VaccineTypes found. '
                'Make sure you ran the seed migration first: python manage.py migrate'
            ))
            return

        self.stdout.write(f'Found {vaccine_types.count()} active vaccine type(s).')

        students = Student.objects.all()
        self.stdout.write(f'Processing {students.count()} student(s)...\n')

        total_created = 0
        total_skipped = 0

        for student in students:
            immunization, imm_created = Immunization.objects.get_or_create(student=student)

            if imm_created:
                self.stdout.write(f'  Created new Immunization record for {student.get_full_name()}')

            student_created = 0
            student_skipped = 0

            for vaccine_type in vaccine_types:
                for schedule in vaccine_type.dose_schedules.all():
                    _, dose_created = VaccineDose.objects.get_or_create(
                        immunization=immunization,
                        vaccine_type=vaccine_type,
                        dose_schedule=schedule,
                    )
                    if dose_created:
                        student_created += 1
                    else:
                        student_skipped += 1

            total_created += student_created
            total_skipped += student_skipped

            if student_created > 0:
                self.stdout.write(
                    f'  ✅  {student.get_full_name()}: '
                    f'{student_created} dose row(s) created, {student_skipped} already existed.'
                )
            else:
                self.stdout.write(
                    f'  —   {student.get_full_name()}: all {student_skipped} dose rows already exist.'
                )

        self.stdout.write('\n' + self.style.SUCCESS(
            f'Done. {total_created} dose row(s) created across all students. '
            f'{total_skipped} already existed and were left untouched.'
        ))