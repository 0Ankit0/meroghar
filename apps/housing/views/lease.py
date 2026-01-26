from ..models import Lease
from apps.iam.models import Organization
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

class LeaseListView(LoginRequiredMixin, ListView):
    model = Lease
    template_name = "housing/lease_list.html"
    context_object_name = "leases"
    
    def get_queryset(self):
        if self.request.active_organization:
            return Lease.objects.filter(organization=self.request.active_organization)
        return Lease.objects.none()

class LeaseCreateView(LoginRequiredMixin, CreateView):
    model = Lease
    fields = ['tenant', 'units', 'start_date', 'end_date', 'rent_amount', 'deposit_amount', 'status']
    template_name = "housing/lease_form.html"
    success_url = reverse_lazy('housing:lease_list')

    def form_valid(self, form):
        user = self.request.user
        
        # Ensure user has an organization context
        if not self.request.active_organization:
            # Create a default organization for the user
            org_name = f"{user.get_full_name() or user.username}'s Properties"
            org = Organization.objects.create(name=org_name)
            
            # Add to M2M
            user.organizations.add(org)
            
            # Set as Active
            self.request.active_organization = org
            self.request.session['active_org_id'] = str(org.id)
            
        form.instance.organization = self.request.active_organization
        return super().form_valid(form)

class LeaseDetailView(LoginRequiredMixin, DetailView):
    model = Lease
    template_name = "housing/lease_detail.html"
    context_object_name = "lease"
    
    def get_queryset(self):
        if self.request.active_organization:
            return Lease.objects.filter(organization=self.request.active_organization)
        return Lease.objects.none()

class LeaseUpdateView(LoginRequiredMixin, UpdateView):
    model = Lease
    fields = ['tenant', 'units', 'start_date', 'end_date', 'rent_amount', 'deposit_amount', 'status']
    template_name = "housing/lease_form.html"
    success_url = reverse_lazy('housing:lease_list')
    
    def get_queryset(self):
        if self.request.active_organization:
            return Lease.objects.filter(organization=self.request.active_organization)
        return Lease.objects.none()

class LeaseDeleteView(LoginRequiredMixin, DeleteView):
    model = Lease
    template_name = "housing/lease_confirm_delete.html"
    success_url = reverse_lazy('housing:lease_list')
    
    def get_queryset(self):
        if self.request.active_organization:
            return Lease.objects.filter(organization=self.request.active_organization)
        return Lease.objects.none()
