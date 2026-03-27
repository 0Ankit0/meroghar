import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('housing', '0005_tenant_user'),
        ('iam', '0004_organizationmembership_refactor_membership'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lead',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=20)),
                ('source', models.CharField(choices=[('WEBSITE', 'Website'), ('REFERRAL', 'Referral'), ('LISTING_SITE', 'Listing Site'), ('WALK_IN', 'Walk-in'), ('OTHER', 'Other')], default='WEBSITE', max_length=20)),
                ('status', models.CharField(choices=[('NEW', 'New'), ('CONTACTED', 'Contacted'), ('QUALIFIED', 'Qualified'), ('CONVERTED', 'Converted'), ('LOST', 'Lost')], default='NEW', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leads', to='iam.organization')),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='LeadFollowUp',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('channel', models.CharField(choices=[('EMAIL', 'Email'), ('PHONE', 'Phone'), ('SMS', 'SMS')], default='EMAIL', max_length=20)),
                ('scheduled_at', models.DateTimeField()),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('DONE', 'Done'), ('SKIPPED', 'Skipped')], default='PENDING', max_length=20)),
                ('message', models.TextField(blank=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follow_ups', to='crm.lead')),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='RentalApplication',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('annual_income', models.DecimalField(decimal_places=2, max_digits=12)),
                ('employment_status', models.CharField(max_length=100)),
                ('employer_name', models.CharField(blank=True, max_length=100)),
                ('references', models.JSONField(blank=True, default=list)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('REVIEW', 'Under Review'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('WITHDRAWN', 'Withdrawn')], default='PENDING', max_length=20)),
                ('submission_date', models.DateField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='crm.lead')),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='housing.unit')),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='Showing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('status', models.CharField(choices=[('SCHEDULED', 'Scheduled'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled'), ('NO_SHOW', 'No Show')], default='SCHEDULED', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='showings', to='crm.lead')),
                ('showing_agent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='showings', to='iam.user')),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='showings', to='housing.unit')),
            ],
            options={'abstract': False},
        ),
    ]
