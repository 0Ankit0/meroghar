from django import forms
from .models import Expense

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'expense_date', 'description', 'property', 'work_order', 'receipt']
        widgets = {
            'expense_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            # Filter properties to organization
            from apps.housing.models import Property
            self.fields['property'].queryset = Property.objects.filter(organization=organization)
            
            # Filter work orders to organization (via unit->property or similar linkage, but WO has no direct org unless through unit)
            # Assuming WorkOrder has a way to filter by org. WorkOrder->Unit->Property->Organization
            from apps.operations.models import WorkOrder
            self.fields['work_order'].queryset = WorkOrder.objects.filter(unit__property__organization=organization)
