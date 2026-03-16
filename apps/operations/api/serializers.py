from rest_framework import serializers
from apps.operations.models import Vendor, WorkOrder

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at']

class WorkOrderSerializer(serializers.ModelSerializer):
    unit_number = serializers.ReadOnlyField(source='unit.unit_number')
    vendor_name = serializers.ReadOnlyField(source='assigned_vendor.name')
    
    class Meta:
        model = WorkOrder
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at']

    def validate(self, attrs):
        request = self.context.get('request')
        active_organization = getattr(request, 'active_organization', None)
        if not active_organization:
            return attrs

        unit = attrs.get('unit') or getattr(self.instance, 'unit', None)
        requester = attrs.get('requester') if 'requester' in attrs else getattr(self.instance, 'requester', None)
        assigned_vendor = attrs.get('assigned_vendor') if 'assigned_vendor' in attrs else getattr(self.instance, 'assigned_vendor', None)

        errors = {}

        if unit and unit.property.organization_id != active_organization.id:
            errors['unit'] = 'Selected unit does not belong to your active organization.'

        if requester and requester.organization_id != active_organization.id:
            errors['requester'] = 'Selected requester does not belong to your active organization.'

        if assigned_vendor and assigned_vendor.organization_id != active_organization.id:
            errors['assigned_vendor'] = 'Selected vendor does not belong to your active organization.'

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'active_organization'):
            validated_data['organization'] = request.active_organization
        return super().create(validated_data)
