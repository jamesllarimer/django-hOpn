# Generated by Django 5.0.6 on 2024-12-23 01:14

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Division',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('skill_level', models.CharField(blank=True, max_length=50)),
                ('age_group', models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Sport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='StripeProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('user_type', models.CharField(choices=[('admin', 'Admin'), ('customer', 'Customer')], default='customer', max_length=10)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to.', related_name='custom_user_set', related_query_name='custom_user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='custom_user_set', related_query_name='custom_user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='League',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('stripe_product_id', models.CharField(blank=True, max_length=255, null=True)),
                ('registration_start_date', models.DateField()),
                ('registration_end_date', models.DateField()),
                ('early_registration_deadline', models.DateField()),
                ('league_start_date', models.DateField()),
                ('league_end_date', models.DateField()),
                ('regular_registration_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('early_registration_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.TextField(blank=True)),
                ('max_teams', models.IntegerField(blank=True, null=True)),
                ('available_divisions', models.ManyToManyField(limit_choices_to={'sport': models.F('sport')}, related_name='league_sessions', to='sportsSignUp.division')),
                ('sport', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leagues', to='sportsSignUp.sport')),
            ],
        ),
        migrations.CreateModel(
            name='FreeAgent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone_number', models.CharField(max_length=20)),
                ('date_of_birth', models.DateField()),
                ('membership_number', models.CharField(max_length=100)),
                ('is_member', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('AVAILABLE', 'Available'), ('INVITED', 'Invited'), ('JOINED', 'Joined'), ('INACTIVE', 'Inactive')], default='AVAILABLE', max_length=20)),
                ('division', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='free_agents', to='sportsSignUp.division')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='free_agent_profiles', to=settings.AUTH_USER_MODEL)),
                ('league', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='free_agents', to='sportsSignUp.league')),
            ],
            options={
                'unique_together': {('user', 'league')},
            },
        ),
        migrations.AddField(
            model_name='division',
            name='sport',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='divisions', to='sportsSignUp.sport'),
        ),
        migrations.CreateModel(
            name='StripePrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=100, unique=True)),
                ('currency', models.CharField(max_length=3)),
                ('unit_amount', models.IntegerField()),
                ('active', models.BooleanField(default=True)),
                ('description', models.TextField(blank=True)),
                ('recurring', models.BooleanField(default=False)),
                ('recurring_interval', models.CharField(blank=True, choices=[('day', 'Day'), ('week', 'Week'), ('month', 'Month'), ('year', 'Year')], max_length=5, null=True)),
                ('recurring_interval_count', models.IntegerField(blank=True, null=True)),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prices', to='sportsSignUp.stripeproduct')),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('signup_code', models.CharField(blank=True, max_length=8, null=True, unique=True)),
                ('division', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teams', to='sportsSignUp.division')),
                ('league', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teams', to='sportsSignUp.league')),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone_number', models.CharField(max_length=20)),
                ('parent_name', models.CharField(blank=True, max_length=200, null=True)),
                ('date_of_birth', models.DateField()),
                ('membership_number', models.CharField(blank=True, max_length=50, null=True)),
                ('is_member', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='linked_players', to=settings.AUTH_USER_MODEL)),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='players', to='sportsSignUp.team')),
            ],
        ),
        migrations.CreateModel(
            name='TeamCaptain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone_number', models.CharField(max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_system_captain', models.BooleanField(default=False)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='team_captains', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='team',
            name='captain',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='captained_teams', to='sportsSignUp.teamcaptain'),
        ),
        migrations.CreateModel(
            name='TeamInvitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('DECLINED', 'Declined'), ('EXPIRED', 'Expired')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('response_at', models.DateTimeField(blank=True, null=True)),
                ('message', models.TextField(blank=True)),
                ('free_agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_invitations', to='sportsSignUp.freeagent')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_invitations', to='sportsSignUp.team')),
            ],
            options={
                'unique_together': {('team', 'free_agent')},
            },
        ),
        migrations.CreateModel(
            name='TeamInvitationNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('invitation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='sportsSignUp.teaminvitation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Registration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('payment_status', models.CharField(choices=[('pending', 'Pending'), ('paid', 'Paid'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded')], default='pending', max_length=50)),
                ('stripe_payment_intent', models.CharField(blank=True, max_length=255, null=True)),
                ('stripe_checkout_session', models.CharField(blank=True, max_length=255, null=True)),
                ('notes', models.TextField(blank=True)),
                ('is_late_registration', models.BooleanField(default=False)),
                ('division', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrations', to='sportsSignUp.division')),
                ('league', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrations', to='sportsSignUp.league')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrations', to='sportsSignUp.player')),
            ],
            options={
                'unique_together': {('player', 'league')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='division',
            unique_together={('name', 'sport')},
        ),
    ]
