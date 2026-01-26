"""Quick script to update templates with MultiIndex fix"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monolithic_agent.settings')

import django
django.setup()

from django.core.management import call_command

print("Updating system templates...")
call_command('create_system_templates')
print("Done!")
