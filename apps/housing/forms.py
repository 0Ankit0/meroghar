from django import forms
from .models import PropertyInspection, InventoryItem, Unit

class PropertyInspectionForm(forms.ModelForm):
    class Meta:
        model = PropertyInspection
        fields = ['inspection_type', 'unit', 'inspector', 'inspection_date', 'status', 'notes', 'condition_rating']
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['unit'].queryset = Unit.objects.filter(property__organization=organization)

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'unit', 'category', 'serial_number', 'purchase_date', 'purchase_price', 'condition', 'notes']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
             self.fields['unit'].queryset = Unit.objects.filter(property__organization=organization)
