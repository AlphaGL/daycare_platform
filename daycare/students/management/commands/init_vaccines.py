"""
Management Command to Initialize CDC Vaccine Schedules
Run this command to populate the database with standard CDC immunization schedules
"""
from django.core.management.base import BaseCommand
from students.models import VaccineType, VaccineDoseSchedule


class Command(BaseCommand):
    help = 'Initialize CDC vaccine schedules in the database'

    def handle(self, *args, **kwargs):
        self.stdout.write('Initializing CDC vaccine schedules...')
        
        # Define all vaccines and their schedules based on CDC recommendations
        vaccines_data = [
            {
                'name': 'Hep B',
                'full_name': 'Hepatitis B',
                'description': 'Protects against hepatitis B virus',
                'total_doses': 3,
                'display_order': 1,
                'doses': [
                    {'dose': 1, 'months': 0, 'cdc_text': '0 mos'},
                    {'dose': 2, 'months': 1, 'min': 1, 'max': 2, 'cdc_text': '1 - 2 mos'},
                    {'dose': 3, 'months': 6, 'min': 6, 'max': 18, 'cdc_text': '6 - 18 mos'},
                ]
            },
            {
                'name': 'DTaP',
                'full_name': 'Diphtheria, Tetanus, acellular Pertussis',
                'description': 'Protects against diphtheria, tetanus, and pertussis (whooping cough)',
                'total_doses': 5,
                'display_order': 2,
                'doses': [
                    {'dose': 1, 'months': 2, 'cdc_text': '2 mos'},
                    {'dose': 2, 'months': 4, 'cdc_text': '4 mos'},
                    {'dose': 3, 'months': 6, 'cdc_text': '6 mos'},
                    {'dose': 4, 'months': 15, 'min': 15, 'max': 18, 'cdc_text': '15 - 18 mos'},
                    {'dose': 5, 'months': 48, 'min': 48, 'max': 72, 'cdc_text': '4 - 6 yrs'},
                ]
            },
            {
                'name': 'Hib',
                'full_name': 'Haemophilus Influenzae Type B',
                'description': 'Protects against Haemophilus influenzae type b',
                'total_doses': 4,
                'display_order': 3,
                'doses': [
                    {'dose': 1, 'months': 2, 'cdc_text': '2 mos'},
                    {'dose': 2, 'months': 4, 'cdc_text': '4 mos'},
                    {'dose': 3, 'months': 6, 'cdc_text': '6 mos'},
                    {'dose': 4, 'months': 12, 'min': 12, 'max': 15, 'cdc_text': '12 - 15 mos'},
                ]
            },
            {
                'name': 'PCV',
                'full_name': 'Pneumococcal Conjugate Vaccine',
                'description': 'Protects against pneumococcal disease',
                'total_doses': 4,
                'display_order': 4,
                'doses': [
                    {'dose': 1, 'months': 2, 'cdc_text': '2 mos'},
                    {'dose': 2, 'months': 4, 'cdc_text': '4 mos'},
                    {'dose': 3, 'months': 6, 'cdc_text': '6 mos'},
                    {'dose': 4, 'months': 12, 'min': 12, 'max': 15, 'cdc_text': '12 - 15 mos'},
                ]
            },
            {
                'name': 'Polio',
                'full_name': 'Inactivated Poliovirus',
                'description': 'Protects against polio',
                'total_doses': 4,
                'display_order': 5,
                'doses': [
                    {'dose': 1, 'months': 2, 'cdc_text': '2 mos'},
                    {'dose': 2, 'months': 4, 'cdc_text': '4 mos'},
                    {'dose': 3, 'months': 6, 'min': 6, 'max': 18, 'cdc_text': '6 - 18 mos'},
                    {'dose': 4, 'months': 48, 'min': 48, 'max': 72, 'cdc_text': '4 - 6 yrs'},
                ]
            },
            {
                'name': 'Rotavirus',
                'full_name': 'Rotavirus',
                'description': 'Protects against rotavirus',
                'total_doses': 3,
                'display_order': 6,
                'doses': [
                    {'dose': 1, 'months': 2, 'cdc_text': '2 mos'},
                    {'dose': 2, 'months': 4, 'cdc_text': '4 mos'},
                    {'dose': 3, 'months': 6, 'cdc_text': '6 mos'},
                ]
            },
            {
                'name': 'Covid',
                'full_name': 'Coronavirus',
                'description': 'Protects against COVID-19',
                'total_doses': 2,
                'display_order': 7,
                'doses': [
                    {'dose': 1, 'months': 6, 'cdc_text': '6 mos'},
                    {'dose': 2, 'months': 6, 'cdc_text': '6 mos'},
                ]
            },
            {
                'name': 'Flu',
                'full_name': 'Seasonal Influenza',
                'description': 'Protects against seasonal flu (yearly)',
                'total_doses': 1,
                'display_order': 8,
                'doses': [
                    {'dose': 1, 'months': 6, 'cdc_text': 'Yearly'},
                ]
            },
            {
                'name': 'MMR',
                'full_name': 'Measles, Mumps, Rubella',
                'description': 'Protects against measles, mumps, and rubella',
                'total_doses': 2,
                'display_order': 9,
                'doses': [
                    {'dose': 1, 'months': 12, 'min': 12, 'max': 15, 'cdc_text': '12 - 15 mos'},
                    {'dose': 2, 'months': 48, 'min': 48, 'max': 72, 'cdc_text': '4 - 6 yrs'},
                ]
            },
            {
                'name': 'VAR',
                'full_name': 'Varicella',
                'description': 'Protects against chickenpox',
                'total_doses': 2,
                'display_order': 10,
                'doses': [
                    {'dose': 1, 'months': 12, 'min': 12, 'max': 15, 'cdc_text': '12 - 15 mos'},
                    {'dose': 2, 'months': 48, 'min': 48, 'max': 72, 'cdc_text': '4 - 6 yrs'},
                ]
            },
            {
                'name': 'Hep A',
                'full_name': 'Hepatitis A',
                'description': 'Protects against hepatitis A',
                'total_doses': 2,
                'display_order': 11,
                'doses': [
                    {'dose': 1, 'months': 12, 'min': 12, 'max': 24, 'cdc_text': '12 - 24 mos'},
                    {'dose': 2, 'months': 12, 'min': 12, 'max': 24, 'cdc_text': '12 - 24 mos'},
                ]
            },
        ]
        
        created_vaccines = 0
        created_doses = 0
        
        for vaccine_data in vaccines_data:
            # Create or update vaccine type
            vaccine, created = VaccineType.objects.update_or_create(
                name=vaccine_data['name'],
                defaults={
                    'full_name': vaccine_data['full_name'],
                    'description': vaccine_data['description'],
                    'total_doses': vaccine_data['total_doses'],
                    'display_order': vaccine_data['display_order'],
                    'is_active': True
                }
            )
            
            if created:
                created_vaccines += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created vaccine: {vaccine.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⟳ Updated vaccine: {vaccine.name}')
                )
            
            # Create dose schedules
            for dose_data in vaccine_data['doses']:
                schedule, created = VaccineDoseSchedule.objects.update_or_create(
                    vaccine_type=vaccine,
                    dose_number=dose_data['dose'],
                    defaults={
                        'recommended_age_months': dose_data['months'],
                        'min_age_months': dose_data.get('min'),
                        'max_age_months': dose_data.get('max'),
                        'cdc_recommendation_text': dose_data['cdc_text'],
                        'is_catch_up': False
                    }
                )
                
                if created:
                    created_doses += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully initialized CDC vaccine schedules!'
            )
        )
        self.stdout.write(f'  - Vaccines: {created_vaccines} created')
        self.stdout.write(f'  - Dose schedules: {created_doses} created')
        self.stdout.write(
            '\nNext steps:'
        )
        self.stdout.write(
            '  1. Existing students will have immunization records auto-created on first access'
        )
        self.stdout.write(
            '  2. New students will have immunization records created automatically'
        )