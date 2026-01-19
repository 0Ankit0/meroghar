from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Property
from apps.iam.models import Organization

class PropertyListView(LoginRequiredMixin, ListView):
    model = Property
    template_name = "housing/property_list.html"
    context_object_name = "properties"
    
    def get_queryset(self):
        # Filter by user's organization
        # For MVP/Demo if no login, return all or empty
        # user = self.request.user
        # if user.is_authenticated and user.organization:
        #     return Property.objects.filter(organization=user.organization)
        return Property.objects.all()

class PropertyCreateView(LoginRequiredMixin, CreateView):
    model = Property
    fields = ['name', 'address', 'city', 'state', 'zip_code']
    template_name = "housing/property_form.html"
    success_url = reverse_lazy('housing:property_list')
    
    def form_valid(self, form):
        user = self.request.user
        
        # Ensure user has an organization
        if not user.organization:
            # Create a default organization for the user (Personal Owner logic)
            org_name = f"{user.get_full_name() or user.username}'s Properties"
            org = Organization.objects.create(name=org_name)
            
            # Assign to user
            user.organization = org
            user.save()
            
        # Assign org to property
        form.instance.organization = user.organization
            
        return super().form_valid(form)

class PropertyDetailView(LoginRequiredMixin, DetailView):
    model = Property
    template_name = "housing/property_detail.html"
    context_object_name = "property"
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Property.objects.filter(organization=user.organization)
        return Property.objects.none()

class PropertyUpdateView(LoginRequiredMixin, UpdateView):
    model = Property
    fields = ['name', 'address', 'city', 'state', 'zip_code', 'amenities']
    template_name = "housing/property_form.html"
    success_url = reverse_lazy('housing:property_list')
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Property.objects.filter(organization=user.organization)
        return Property.objects.none()

class PropertyDeleteView(LoginRequiredMixin, DeleteView):
    model = Property
    template_name = "housing/property_confirm_delete.html"
    success_url = reverse_lazy('housing:property_list')
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Property.objects.filter(organization=user.organization)
        return Property.objects.none()
