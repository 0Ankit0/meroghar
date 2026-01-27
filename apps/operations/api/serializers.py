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

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'active_organization'):
            validated_data['organization'] = request.active_organization
        return super().create(validated_data)
