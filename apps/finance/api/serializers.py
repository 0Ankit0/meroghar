from rest_framework import serializers
from apps.finance.models import Expense, Invoice, Payment

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at']

    def validate(self, attrs):
        request = self.context.get('request')
        active_organization = getattr(request, 'active_organization', None)
        if not active_organization:
            return attrs

        property_obj = attrs.get('property') or getattr(self.instance, 'property', None)
        unit = attrs.get('unit') if 'unit' in attrs else getattr(self.instance, 'unit', None)
        work_order = attrs.get('work_order') if 'work_order' in attrs else getattr(self.instance, 'work_order', None)

        errors = {}

        if property_obj and property_obj.organization_id != active_organization.id:
            errors['property'] = 'Selected property does not belong to your active organization.'

        if unit:
            if unit.property.organization_id != active_organization.id:
                errors['unit'] = 'Selected unit does not belong to your active organization.'
            elif property_obj and unit.property_id != property_obj.id:
                errors['unit'] = 'Selected unit does not belong to the selected property.'

        if work_order:
            if work_order.organization_id != active_organization.id:
                errors['work_order'] = 'Selected work order does not belong to your active organization.'
            elif property_obj and work_order.unit.property_id != property_obj.id:
                errors['work_order'] = 'Selected work order is not for the selected property.'
            elif unit and work_order.unit_id != unit.id:
                errors['work_order'] = 'Selected work order is not for the selected unit.'

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'active_organization'):
            validated_data['organization'] = request.active_organization
        return super().create(validated_data)

class InvoiceSerializer(serializers.ModelSerializer):
    balance_due = serializers.ReadOnlyField()
    lease_units = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at', 'invoice_number', 'paid_amount', 'status']

    def get_lease_units(self, obj):
        if obj.lease:
            return ", ".join([u.unit_number for u in obj.lease.units.all()])
        return ""

class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.ReadOnlyField(source='invoice.invoice_number')
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at', 'status', 'verified_at', 'transaction_id']

    def validate(self, attrs):
        request = self.context.get('request')
        active_organization = getattr(request, 'active_organization', None)
        if not active_organization:
            return attrs

        invoice = attrs.get('invoice') if 'invoice' in attrs else getattr(self.instance, 'invoice', None)
        if invoice and invoice.organization_id != active_organization.id:
            raise serializers.ValidationError(
                {'invoice': 'Selected invoice does not belong to your active organization.'}
            )

        return attrs
