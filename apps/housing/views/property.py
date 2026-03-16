from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Property
from apps.iam.models import Organization, OrganizationMembership

class PropertyListView(LoginRequiredMixin, ListView):
    model = Property
    template_name = "housing/property_list.html"
    context_object_name = "properties"
    
    def get_queryset(self):
        if self.request.active_organization:
            return Property.objects.filter(organization=self.request.active_organization)
        return Property.objects.none()

class PropertyCreateView(LoginRequiredMixin, CreateView):
    model = Property
    fields = ['name', 'address', 'city', 'state', 'zip_code']
    template_name = "housing/property_form.html"
    success_url = reverse_lazy('housing:property_list')
    
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
            
        # Assign org to property
        form.instance.organization = self.request.active_organization
            
        return super().form_valid(form)

class PropertyDetailView(LoginRequiredMixin, DetailView):
    model = Property
    template_name = "housing/property_detail.html"
    context_object_name = "property"
    
    def get_queryset(self):
        if self.request.active_organization:
             return Property.objects.filter(organization=self.request.active_organization)
        return Property.objects.none()

class PropertyUpdateView(LoginRequiredMixin, UpdateView):
    model = Property
    fields = ['name', 'address', 'city', 'state', 'zip_code', 'amenities']
    template_name = "housing/property_form.html"
    success_url = reverse_lazy('housing:property_list')
    
    def get_queryset(self):
        if self.request.active_organization:
             return Property.objects.filter(organization=self.request.active_organization)
        return Property.objects.none()

class PropertyDeleteView(LoginRequiredMixin, DeleteView):
    model = Property
    template_name = "housing/property_confirm_delete.html"
    success_url = reverse_lazy('housing:property_list')
    
    def get_queryset(self):
        if self.request.active_organization:
             return Property.objects.filter(organization=self.request.active_organization)
        return Property.objects.none()
