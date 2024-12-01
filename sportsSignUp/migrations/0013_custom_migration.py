from django.db import migrations, models
import random
import string

def generate_unique_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def assign_signup_codes(apps, schema_editor):
    Team = apps.get_model('sportsSignUp', 'Team')
    used_codes = set()
    
    for team in Team.objects.all():
        while True:
            code = generate_unique_code()
            if code not in used_codes:
                team.signup_code = code
                used_codes.add(code)
                team.save()
                break

class Migration(migrations.Migration):

    dependencies = [
        ('sportsSignUp', '0012_remove_player_joined_team_date_alter_player_team'),  # Replace with your previous migration
    ]

    operations = [
        # First add the field as nullable
        migrations.AddField(
            model_name='team',
            name='signup_code',
            field=models.CharField(max_length=8, null=True, blank=True, unique=True),
        ),
        
        # Run the function to assign unique codes
        migrations.RunPython(assign_signup_codes),
        
        # Then make it non-nullable
        migrations.AlterField(
            model_name='team',
            name='signup_code',
            field=models.CharField(max_length=8, unique=True),
        ),
    ]