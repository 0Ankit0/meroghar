from rest_framework import serializers
from apps.iam.models import User, Organization


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
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
