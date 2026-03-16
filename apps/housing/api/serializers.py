from rest_framework import serializers
from apps.housing.models import PropertyInspection, InventoryItem, InspectionPhoto, Property, Unit, Tenant, Lease

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
