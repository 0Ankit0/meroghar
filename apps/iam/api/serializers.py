from rest_framework import serializers

from apps.iam.models import User, Organization, OrganizationMembership



class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug']


class UserSerializer(serializers.ModelSerializer):
    organizations_detail = OrganizationSerializer(source='organizations', many=True, read_only=True)
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name',
            'role', 'organizations', 'organizations_detail',
            'is_active', 'date_joined',
            'verification_status', 'is_verified',
            'provisioned_by_owner', 'verified_by_superuser',
            'verified_at', 'verified_by', 'created_by',
            'delegated_by', 'delegated_at',
        ]
        read_only_fields = [
            'organizations_detail', 'is_active', 'date_joined',
            'verification_status', 'is_verified',
            'provisioned_by_owner', 'verified_by_superuser',
            'verified_at', 'verified_by', 'created_by',
            'delegated_by', 'delegated_at',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def validate(self, attrs):
        request = self.context.get('request')
        active_org = getattr(request, 'active_organization', None) if request else None
        if request and request.user and not request.user.is_superuser and active_org:
            allowed_roles = {OrganizationMembership.Role.OWNER, OrganizationMembership.Role.ADMIN}
            if not request.user.has_org_role(active_org, allowed_roles):
                raise serializers.ValidationError('Insufficient organization role for this action.')
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()

        request = self.context.get('request')
        active_org = getattr(request, 'active_organization', None) if request else None
        if active_org and request and request.user:
            OrganizationMembership.objects.update_or_create(
                organization=active_org,
                user=user,
                defaults={
                    'role': validated_data.get('role', OrganizationMembership.Role.STAFF),
                    'is_active': True,
                    'invited_by': request.user,
                },
            )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()

        request = self.context.get('request')
        active_org = getattr(request, 'active_organization', None) if request else None
        if active_org and request and request.user:
            OrganizationMembership.objects.update_or_create(
                organization=active_org,
                user=user,
                defaults={
                    'role': validated_data.get('role', user.role),
                    'is_active': validated_data.get('is_active', user.is_active),
                    'invited_by': request.user,
                },
            )
        return user
