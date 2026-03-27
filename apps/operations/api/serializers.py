from rest_framework import serializers
from django.utils import timezone
from apps.operations.models import Vendor, WorkOrder
from apps.finance.models import Expense

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at']

class WorkOrderSerializer(serializers.ModelSerializer):
    unit_number = serializers.ReadOnlyField(source='unit.unit_number')
    vendor_name = serializers.ReadOnlyField(source='assigned_vendor.company_name')
    
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
        work_order = super().create(validated_data)
        self._auto_assign_vendor_if_needed(work_order)
        self._create_resolution_expense_if_needed(work_order)
        return work_order

    def update(self, instance, validated_data):
        work_order = super().update(instance, validated_data)
        self._auto_assign_vendor_if_needed(work_order)
        self._create_resolution_expense_if_needed(work_order)
        return work_order

    def _auto_assign_vendor_if_needed(self, work_order):
        if work_order.assigned_vendor_id:
            return
        vendor = Vendor.objects.filter(
            organization=work_order.organization,
            is_active=True,
            service_type=work_order.preferred_service_type,
        ).order_by('created_at').first()
        if vendor:
            work_order.assigned_vendor = vendor
            work_order.vendor_auto_assigned_at = timezone.now()
            work_order.save(update_fields=['assigned_vendor', 'vendor_auto_assigned_at', 'updated_at'])

    def _create_resolution_expense_if_needed(self, work_order):
        if work_order.status not in [WorkOrder.Status.RESOLVED, WorkOrder.Status.CLOSED]:
            return
        if not work_order.assigned_vendor or not work_order.actual_hours:
            return
        if Expense.objects.filter(work_order=work_order).exists():
            return
        rate = work_order.assigned_vendor.hourly_rate
        if not rate:
            return

        Expense.objects.create(
            organization=work_order.organization,
            property=work_order.unit.property,
            unit=work_order.unit,
            work_order=work_order,
            category=Expense.Category.MAINTENANCE,
            amount=rate * work_order.actual_hours,
            expense_date=timezone.now().date(),
            description=f"Auto-created from work order {work_order.id}",
        )
