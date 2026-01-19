from django.views.generic import DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from ..models import Organization

class OrganizationDetailView(LoginRequiredMixin, DetailView):
    model = Organization
    template_name = "iam/organization_detail.html"
    context_object_name = "organization"

    def get_object(self, queryset=None):
        # Always return the user's organization
        return self.request.user.organization

class OrganizationUpdateView(LoginRequiredMixin, UpdateView):
    model = Organization
    fields = ['name', 'address']
    template_name = "iam/organization_form.html"
    success_url = reverse_lazy('iam:organization_detail')
    
    def get_object(self, queryset=None):
        # Refresh from DB to ensure we have the latest relation
        self.request.user.refresh_from_db()
        org = self.request.user.organization
        if not org:
             # Should not happen if they are on this page, but as fallback
             from django.http import Http404
             raise Http404("You do not have an organization.")
        return org
