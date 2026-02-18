from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(SchoolProfile)
admin.site.register(SchoolSettings)
admin.site.register(Reminder)