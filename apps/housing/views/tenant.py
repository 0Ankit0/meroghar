from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Tenant
from apps.iam.models import Organization

class TenantListView(LoginRequiredMixin, ListView):
    model = Tenant
    template_name = "housing/tenant_list.html"
    context_object_name = "tenants"

class TenantCreateView(LoginRequiredMixin, CreateView):
    model = Tenant
    fields = ['first_name', 'last_name', 'email', 'phone', 'id_number', 'emergency_contact_name', 'emergency_contact_phone']
    template_name = "housing/tenant_form.html"
    success_url = reverse_lazy('housing:tenant_list')

    def form_valid(self, form):
        user = self.request.user
        if not user.organization:
            # Create default org if missing
            org_name = f"{user.get_full_name() or user.username}'s Properties"
            org = Organization.objects.create(name=org_name)
            user.organization = org
            user.save()
        
        form.instance.organization = user.organization
        return super().form_valid(form)

class TenantDetailView(LoginRequiredMixin, DetailView):
    model = Tenant
    template_name = "housing/tenant_detail.html"
    context_object_name = "tenant"
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Tenant.objects.filter(organization=user.organization)
        return Tenant.objects.none()

class TenantUpdateView(LoginRequiredMixin, UpdateView):
    model = Tenant
    fields = ['first_name', 'last_name', 'email', 'phone', 'id_number', 'emergency_contact_name', 'emergency_contact_phone']
    template_name = "housing/tenant_form.html"
    success_url = reverse_lazy('housing:tenant_list')
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Tenant.objects.filter(organization=user.organization)
        return Tenant.objects.none()

class TenantDeleteView(LoginRequiredMixin, DeleteView):
    model = Tenant
    template_name = "housing/tenant_confirm_delete.html"
    success_url = reverse_lazy('housing:tenant_list')
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Tenant.objects.filter(organization=user.organization)
        return Tenant.objects.none()
