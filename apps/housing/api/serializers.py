from rest_framework import serializers
from apps.housing.models import PropertyInspection, InventoryItem, InspectionPhoto, Property, Unit, Tenant, Lease, LeaseRenewal

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at']

class UnitSerializer(serializers.ModelSerializer):
    property_name = serializers.ReadOnlyField(source='property.name')
    
    class Meta:
        model = Unit
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class TenantSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='full_name')
    
    class Meta:
        model = Tenant
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at']

class LeaseSerializer(serializers.ModelSerializer):
    unit_numbers = serializers.SerializerMethodField()
    tenant_name = serializers.ReadOnlyField(source='tenant.full_name')

    def get_unit_numbers(self, obj):
        return list(obj.units.values_list('unit_number', flat=True))
    
    class Meta:
        model = Lease
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, attrs):
        request = self.context.get('request')
        active_organization = getattr(request, 'active_organization', None)
        if not active_organization:
            return attrs

        tenant = attrs.get('tenant') or getattr(self.instance, 'tenant', None)

        if 'units' in attrs:
            units = attrs.get('units')
        elif self.instance:
            units = self.instance.units.all()
        else:
            units = []

        errors = {}

        if tenant and tenant.organization_id != active_organization.id:
            errors['tenant'] = 'Selected tenant does not belong to your active organization.'

        invalid_unit_numbers = [unit.unit_number for unit in units if unit.property.organization_id != active_organization.id]
        if invalid_unit_numbers:
            errors['units'] = (
                'One or more selected units do not belong to your active organization: '
                f"{', '.join(invalid_unit_numbers)}."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

class InspectionPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionPhoto
        fields = ['id', 'photo', 'caption', 'created_at']

class PropertyInspectionSerializer(serializers.ModelSerializer):
    photos = InspectionPhotoSerializer(many=True, read_only=True)
    property_name = serializers.ReadOnlyField(source='unit.property.name')
    unit_number = serializers.ReadOnlyField(source='unit.unit_number')
    inspector_name = serializers.ReadOnlyField(source='inspector.get_full_name')
    
    class Meta:
        model = PropertyInspection
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at']

class InventoryItemSerializer(serializers.ModelSerializer):
    unit_number = serializers.ReadOnlyField(source='unit.unit_number')
    
    class Meta:
        model = InventoryItem
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at']


class LeaseRenewalSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaseRenewal
        fields = '__all__'
        read_only_fields = ['reviewed_by', 'reviewed_at', 'renewal_lease', 'created_at', 'updated_at']
