from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from ..models import OrganizationGroup
from django import forms

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        # Allow superusers or staff
        return self.request.user.is_superuser or self.request.user.is_staff

class OrganizationGroupListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = OrganizationGroup
    template_name = "iam/group_list.html"
    context_object_name = "groups"

class OrganizationGroupCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = OrganizationGroup
    fields = ['name', 'description', 'organizations', 'members', 'permissions']
    template_name = "iam/group_form.html"
    success_url = reverse_lazy('iam:group_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Customize widgets for M2M if needed, e.g., checkbox select multiple
        form.fields['organizations'].widget = forms.CheckboxSelectMultiple()
        form.fields['members'].widget = forms.CheckboxSelectMultiple()
        # permissions can be large, maybe FilteredSelectMultiple if using admin widgets, but here standard select or checkbox
        return form

class OrganizationGroupUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = OrganizationGroup
    fields = ['name', 'description', 'organizations', 'members', 'permissions']
    template_name = "iam/group_form.html"
    success_url = reverse_lazy('iam:group_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['organizations'].widget = forms.CheckboxSelectMultiple()
        form.fields['members'].widget = forms.CheckboxSelectMultiple()
        return form

class OrganizationGroupDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = OrganizationGroup
    template_name = "iam/group_confirm_delete.html"
    success_url = reverse_lazy('iam:group_list')
