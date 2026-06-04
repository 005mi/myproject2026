from django.apps import AppConfig


class ResearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'research'

    def ready(self):
        import research.signals
        
        # TODO: Temporary code to reset admin password. Remove after login.
        try:
            from django.contrib.auth.models import User
            admin_user = User.objects.filter(username="admin").first() or User.objects.filter(is_superuser=True).first()
            if admin_user:
                admin_user.set_password("admin1234")
                admin_user.save()
                print("TEMP: Successfully reset admin password to 'admin1234'")
            else:
                User.objects.create_superuser("admin", "admin@example.com", "admin1234")
                print("TEMP: Successfully created 'admin' superuser with password 'admin1234'")
        except Exception as e:
            print("TEMP: Could not reset admin password:", e)