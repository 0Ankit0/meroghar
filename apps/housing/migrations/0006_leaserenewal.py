import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('housing', '0005_tenant_user'),
        ('iam', '0004_organizationmembership_refactor_membership'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeaseRenewal',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('proposed_start_date', models.DateField()),
                ('proposed_end_date', models.DateField()),
                ('proposed_rent_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('notes', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('REQUESTED', 'Requested'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='DRAFT', max_length=20)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('lease', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='renewals', to='housing.lease')),
                ('renewal_lease', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source_renewals', to='housing.lease')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_renewals', to='iam.user')),
            ],
            options={'abstract': False},
        ),
    ]
