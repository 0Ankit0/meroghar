from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0002_vendor_workorder_assigned_vendor'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='actual_hours',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='workorder',
            name='preferred_service_type',
            field=models.CharField(choices=[('PLUMBING', 'Plumbing'), ('ELECTRICAL', 'Electrical'), ('HVAC', 'HVAC'), ('GENERAL', 'General Maintenance'), ('CLEANING', 'Cleaning'), ('LANDSCAPING', 'Landscaping'), ('OTHER', 'Other')], default='GENERAL', max_length=20),
        ),
        migrations.AddField(
            model_name='workorder',
            name='vendor_auto_assigned_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
