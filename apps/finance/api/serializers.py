from rest_framework import serializers
from apps.finance.models import Expense, Invoice, Payment

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at']

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
