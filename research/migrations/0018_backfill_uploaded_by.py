from django.db import migrations

def backfill_uploaded_by(apps, schema_editor):
    Project = apps.get_model('research', 'Project')
    User = apps.get_model('auth', 'User')
    
    for project in Project.objects.filter(uploaded_by__isnull=True):
        # Try to find a user whose username matches the student_name (the old behavior)
        user = User.objects.filter(username=project.student_name).first()
        if user:
            project.uploaded_by = user
            project.save()

class Migration(migrations.Migration):

    dependencies = [
        ('research', '0017_project_uploaded_by'),
    ]

    operations = [
        migrations.RunPython(backfill_uploaded_by),
    ]
