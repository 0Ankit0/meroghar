from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Tenant
from apps.iam.models import Organization, OrganizationMembership
from apps.finance.models import Payment
from apps.operations.models import WorkOrder

class TenantListView(LoginRequiredMixin, ListView):
    model = Tenant
    template_name = "housing/tenant_list.html"
    context_object_name = "tenants"

    def get_queryset(self):
        if self.request.active_organization:
            return Tenant.objects.filter(organization=self.request.active_organization)
        return Tenant.objects.none()

class TenantCreateView(LoginRequiredMixin, CreateView):
    model = Tenant
    fields = ['first_name', 'last_name', 'email', 'phone', 'id_proof_number', 'emergency_contact_name', 'emergency_contact_phone']
    template_name = "housing/tenant_form.html"
    success_url = reverse_lazy('housing:tenant_list')

    def form_valid(self, form):
        user = self.request.user
        
        # Ensure user has an organization context
        if not self.request.active_organization:
            # Create a default organization for the user
            org_name = f"{user.get_full_name() or user.username}'s Properties"
            org = Organization.objects.create(name=org_name)
            
            # Add to M2M
            OrganizationMembership.objects.get_or_create(
                organization=org,
                user=user,
                defaults={'role': OrganizationMembership.Role.OWNER, 'invited_by': user},
            )
            
            # Set as Active
            self.request.active_organization = org
            self.request.session['active_org_id'] = str(org.id)
            
        form.instance.organization = self.request.active_organization
        return super().form_valid(form)

class TenantDetailView(LoginRequiredMixin, DetailView):
    model = Tenant
    template_name = "housing/tenant_detail.html"
    context_object_name = "tenant"
    
    def get_queryset(self):
        if self.request.active_organization:
            return Tenant.objects.filter(organization=self.request.active_organization)
        return Tenant.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.get_object()
        
        # Related data
        context['leases'] = tenant.leases.all().order_by('-start_date')
        context['work_orders'] = tenant.requested_work_orders.all().order_by('-created_at')
        context['payments'] = Payment.objects.filter(invoice__lease__tenant=tenant).order_by('-created_at')
        
        return context

class TenantUpdateView(LoginRequiredMixin, UpdateView):
    model = Tenant
    fields = ['first_name', 'last_name', 'email', 'phone', 'id_proof_number', 'emergency_contact_name', 'emergency_contact_phone']
    template_name = "housing/tenant_form.html"
    success_url = reverse_lazy('housing:tenant_list')
    
    def get_queryset(self):
        if self.request.active_organization:
            return Tenant.objects.filter(organization=self.request.active_organization)
        return Tenant.objects.none()

class TenantDeleteView(LoginRequiredMixin, DeleteView):
    model = Tenant
    template_name = "housing/tenant_confirm_delete.html"
    success_url = reverse_lazy('housing:tenant_list')
    
    def get_queryset(self):
        if self.request.active_organization:
            return Tenant.objects.filter(organization=self.request.active_organization)
        return Tenant.objects.none()
