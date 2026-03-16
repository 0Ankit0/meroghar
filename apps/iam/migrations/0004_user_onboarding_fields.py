from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('iam', '0003_remove_user_organization_organizationgroup'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_accounts', to='iam.user'),
        ),
        migrations.AddField(
            model_name='user',
            name='delegated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='delegated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='delegated_accounts', to='iam.user'),
        ),
        migrations.AddField(
            model_name='user',
            name='provisioned_by_owner',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='verification_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('VERIFIED', 'Verified'), ('REJECTED', 'Rejected')], default='VERIFIED', max_length=20),
        ),
        migrations.AddField(
            model_name='user',
            name='verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='verified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_accounts', to='iam.user'),
        ),
        migrations.AddField(
            model_name='user',
            name='verified_by_superuser',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='UserOnboardingEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('event_type', models.CharField(choices=[('CREATED', 'Created'), ('VERIFIED', 'Verified'), ('OWNER_ASSIGNED', 'Owner Assigned'), ('MEMBER_DELEGATED', 'Member Delegated')], max_length=32)),
                ('notes', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='onboarding_events', to='iam.user')),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='account_actions', to='iam.user')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
