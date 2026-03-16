from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.iam.models import User, Organization

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug']

class UserSerializer(serializers.ModelSerializer):
    organizations_detail = OrganizationSerializer(source='organizations', many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'organizations', 'organizations_detail', 'is_active', 'date_joined']
        read_only_fields = ['organizations_detail', 'is_active', 'date_joined']
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


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get('request')
        user = authenticate(request=request, username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid username or password.')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')
        attrs['user'] = user
        return attrs


class MembershipSerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'is_active']

    def get_is_active(self, obj):
        active_organization = self.context.get('active_organization')
        return bool(active_organization and str(active_organization.id) == str(obj.id))


class SwitchOrganizationSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()


class AuthProfileSerializer(serializers.ModelSerializer):
    memberships = MembershipSerializer(source='organizations', many=True, read_only=True)
    active_organization = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'memberships',
            'active_organization',
        ]

    def get_active_organization(self, user):
        active_organization = self.context.get('active_organization')
        if not active_organization:
            return None
        return MembershipSerializer(
            active_organization,
            context={'active_organization': active_organization},
        ).data
