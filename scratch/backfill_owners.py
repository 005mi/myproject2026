import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from research.models import Project
from django.contrib.auth.models import User

print("Starting back-fill...")
projects = Project.objects.filter(uploaded_by__isnull=True)
count = 0
for p in projects:
    user = User.objects.filter(username=p.student_name).first()
    if user:
        p.uploaded_by = user
        p.save()
        print(f"Updated: {p.title_th} -> Owner: {user.username}")
        count += 1

print(f"Finished. Total updated: {count}")
