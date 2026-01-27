from django import forms
from .models import Lead, Showing, RentalApplication

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['first_name', 'last_name', 'email', 'phone', 'source', 'status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class ShowingForm(forms.ModelForm):
    class Meta:
        model = Showing
        fields = ['lead', 'unit', 'showing_agent', 'start_time', 'end_time', 'status', 'notes']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class RentalApplicationForm(forms.ModelForm):
    class Meta:
        model = RentalApplication
        fields = ['lead', 'unit', 'annual_income', 'employment_status', 'employer_name', 'status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
