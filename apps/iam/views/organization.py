from django.views.generic import DetailView, UpdateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404

from ..models import Organization, OrganizationMembership


class OrganizationDetailView(LoginRequiredMixin, DetailView):
    model = Organization
    template_name = "iam/organization_detail.html"
    context_object_name = "organization"

    def get_object(self, queryset=None):
        return self.request.active_organization


class OrganizationUpdateView(LoginRequiredMixin, UpdateView):
    model = Organization
    fields = ['name', 'address']
    template_name = "iam/organization_form.html"
    success_url = reverse_lazy('iam:organization_detail')

    def get_object(self, queryset=None):
        org = self.request.active_organization
        if not org:
            raise Http404("No active organization selected.")
        return org


class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = "iam/organization_list.html"
    context_object_name = "organizations"

    def get_queryset(self):
        return Organization.objects.filter(
            memberships__user=self.request.user,
            memberships__is_active=True,
        ).distinct()


class OrganizationCreateView(LoginRequiredMixin, CreateView):
    model = Organization
    fields = ['name', 'address', 'phone', 'email', 'website']
    template_name = "iam/organization_form.html"
    success_url = reverse_lazy('iam:organization_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        OrganizationMembership.objects.create(
            organization=self.object,
            user=self.request.user,
            role=OrganizationMembership.Role.OWNER,
            invited_by=self.request.user,
        )
        self.request.session['active_org_id'] = str(self.object.id)
        return response


from django.views import View


class SwitchOrganizationView(LoginRequiredMixin, View):
    def post(self, request, pk):
        org = get_object_or_404(
            Organization,
            pk=pk,
            memberships__user=request.user,
            memberships__is_active=True,
        )
        request.session['active_org_id'] = str(org.id)
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', reverse_lazy('core:dashboard')))
        return redirect(next_url)
