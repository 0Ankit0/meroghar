import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


def migrate_existing_memberships(apps, schema_editor):
    User = apps.get_model('iam', 'User')
    OrganizationMembership = apps.get_model('iam', 'OrganizationMembership')

    through_model = User.organizations.through

    org_to_user_ids = {}
    for row in through_model.objects.all().values_list('organization_id', 'user_id'):
        org_id, user_id = row
        org_to_user_ids.setdefault(org_id, []).append(user_id)

    for org_id, user_ids in org_to_user_ids.items():
        owner_id = user_ids[0] if user_ids else None
        for user_id in user_ids:
            user = User.objects.get(pk=user_id)
            role = 'OWNER' if user_id == owner_id else (user.role or 'STAFF')
            OrganizationMembership.objects.update_or_create(
                organization_id=org_id,
                user_id=user_id,
                defaults={
                    'role': role,
                    'is_active': True,
                    'invited_by_id': owner_id,
                },
            )


def reverse_migrate_memberships(apps, schema_editor):
    User = apps.get_model('iam', 'User')
    OrganizationMembership = apps.get_model('iam', 'OrganizationMembership')
    through_model = User.organizations.through

    for membership in OrganizationMembership.objects.filter(is_active=True).values_list('organization_id', 'user_id'):
        through_model.objects.get_or_create(organization_id=membership[0], user_id=membership[1])


class Migration(migrations.Migration):

    dependencies = [
        ('iam', '0003_remove_user_organization_organizationgroup'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationMembership',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('role', models.CharField(choices=[('OWNER', 'Owner'), ('ADMIN', 'Admin'), ('MANAGER', 'Manager'), ('STAFF', 'Staff'), ('TENANT', 'Tenant'), ('VENDOR', 'Vendor')], default='STAFF', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('invited_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_organization_invites', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='iam.organization')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organization_memberships', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(migrate_existing_memberships, reverse_migrate_memberships),
        migrations.RemoveField(
            model_name='user',
            name='organizations',
        ),
        migrations.AddConstraint(
            model_name='organizationmembership',
            constraint=models.UniqueConstraint(fields=('organization', 'user'), name='iam_unique_org_user_membership'),
        ),
        migrations.AddConstraint(
            model_name='organizationmembership',
            constraint=models.UniqueConstraint(condition=Q(is_active=True, role='OWNER'), fields=('organization',), name='iam_unique_active_owner_per_org'),
        ),
    ]
