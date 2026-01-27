from django import forms
from .models import Vendor, WorkOrder

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['company_name', 'contact_person', 'email', 'phone', 'service_type', 'hourly_rate', 'address', 'is_active']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = ['unit', 'title', 'description', 'priority', 'status', 'assigned_to', 'assigned_vendor']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['assigned_vendor'].queryset = Vendor.objects.filter(organization=organization, is_active=True)
