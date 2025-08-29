# accounts/migrations/0002_create_superuser.py (CORRECTED VERSION)

from django.db import migrations

def create_superuser(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('accounts', 'UserProfile')

    # Check if the superuser already exists
    if not User.objects.filter(username='Administrator').exists():
        # create_superuser is a method on the manager, so it's safe to use
        superuser = User.objects.create_superuser(
            username='Administrator',
            email='administrator@medcare.com',
            password='Admin@123'
        )
        # We need to create the UserProfile separately
        UserProfile.objects.create(user=superuser, role='ADMIN')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]