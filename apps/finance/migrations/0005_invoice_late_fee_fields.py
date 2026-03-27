from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0004_expense'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='late_fee_amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='invoice',
            name='late_fee_applied_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
