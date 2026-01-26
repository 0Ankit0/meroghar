from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Unit, Property

class UnitListView(LoginRequiredMixin, ListView):
    model = Unit
    template_name = "housing/unit_list.html"
    context_object_name = "units"

    def get_queryset(self):
        if self.request.active_organization:
            return Unit.objects.filter(property__organization=self.request.active_organization).select_related('property')
        return Unit.objects.none()

class UnitCreateView(LoginRequiredMixin, CreateView):
    model = Unit
    fields = ['property', 'unit_number', 'floor', 'rent_amount', 'status', 'bedrooms', 'bathrooms', 'area_sqft', 'market_rent']
    template_name = "housing/unit_form.html"
    success_url = reverse_lazy('housing:unit_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.active_organization:
             form.fields['property'].queryset = Property.objects.filter(organization=self.request.active_organization)
        else:
             form.fields['property'].queryset = Property.objects.none()
        return form

class UnitDetailView(LoginRequiredMixin, DetailView):
    model = Unit
    template_name = "housing/unit_detail.html"
    context_object_name = "unit"
    
    def get_queryset(self):
        if self.request.active_organization:
            return Unit.objects.filter(property__organization=self.request.active_organization).select_related('property')
        return Unit.objects.none()

class UnitUpdateView(LoginRequiredMixin, UpdateView):
    model = Unit
    fields = ['property', 'unit_number', 'floor', 'rent_amount', 'status', 'bedrooms', 'bathrooms', 'area_sqft', 'market_rent']
    template_name = "housing/unit_form.html"
    success_url = reverse_lazy('housing:unit_list')
    
    def get_queryset(self):
        if self.request.active_organization:
            return Unit.objects.filter(property__organization=self.request.active_organization)
        return Unit.objects.none()

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.active_organization:
             form.fields['property'].queryset = Property.objects.filter(organization=self.request.active_organization)
        else:
             form.fields['property'].queryset = Property.objects.none()
        return form

class UnitDeleteView(LoginRequiredMixin, DeleteView):
    model = Unit
    template_name = "housing/unit_confirm_delete.html"
    success_url = reverse_lazy('housing:unit_list')
    
    def get_queryset(self):
        if self.request.active_organization:
            return Unit.objects.filter(property__organization=self.request.active_organization)
        return Unit.objects.none()
