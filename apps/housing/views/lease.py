from ..models import Lease
from apps.iam.models import Organization
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

class LeaseListView(LoginRequiredMixin, ListView):
    model = Lease
    template_name = "housing/lease_list.html"
    context_object_name = "leases"

class LeaseCreateView(LoginRequiredMixin, CreateView):
    model = Lease
    fields = ['tenant', 'unit', 'start_date', 'end_date', 'rent_amount', 'deposit_amount', 'status']
    template_name = "housing/lease_form.html"
    success_url = reverse_lazy('housing:lease_list')

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

class LeaseDetailView(LoginRequiredMixin, DetailView):
    model = Lease
    template_name = "housing/lease_detail.html"
    context_object_name = "lease"
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Lease.objects.filter(organization=user.organization)
        return Lease.objects.none()

class LeaseUpdateView(LoginRequiredMixin, UpdateView):
    model = Lease
    fields = ['tenant', 'unit', 'start_date', 'end_date', 'rent_amount', 'deposit_amount', 'status']
    template_name = "housing/lease_form.html"
    success_url = reverse_lazy('housing:lease_list')
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Lease.objects.filter(organization=user.organization)
        return Lease.objects.none()

class LeaseDeleteView(LoginRequiredMixin, DeleteView):
    model = Lease
    template_name = "housing/lease_confirm_delete.html"
    success_url = reverse_lazy('housing:lease_list')
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Lease.objects.filter(organization=user.organization)
        return Lease.objects.none()
