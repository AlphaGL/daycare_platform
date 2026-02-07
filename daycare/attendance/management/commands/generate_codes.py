# attendance/management/commands/generate_codes.py
from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        parents = User.objects.filter(role='PARENT', check_in_code='')
        for parent in parents:
            parent.generate_check_in_code()
            self.stdout.write(f"Generated code for {parent.get_full_name()}")