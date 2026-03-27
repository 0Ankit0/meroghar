from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from apps.housing.models import LeaseRenewal


class LeaseRenewalListView(LoginRequiredMixin, ListView):
    model = LeaseRenewal
    template_name = 'housing/lease_renewal_list.html'
    context_object_name = 'renewals'

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if not active_org:
            return LeaseRenewal.objects.none()
        return LeaseRenewal.objects.filter(lease__organization=active_org).order_by('-created_at')


class LeaseRenewalCreateView(LoginRequiredMixin, CreateView):
    model = LeaseRenewal
    fields = ['lease', 'proposed_start_date', 'proposed_end_date', 'proposed_rent_amount', 'notes', 'status']
    template_name = 'housing/lease_renewal_form.html'
    success_url = reverse_lazy('housing:lease_renewal_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        active_org = getattr(self.request, 'active_organization', None)
        if active_org:
            form.fields['lease'].queryset = form.fields['lease'].queryset.filter(organization=active_org)
        return form


class LeaseRenewalUpdateView(LoginRequiredMixin, UpdateView):
    model = LeaseRenewal
    fields = ['status', 'notes']
    template_name = 'housing/lease_renewal_form.html'
    success_url = reverse_lazy('housing:lease_renewal_list')

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if not active_org:
            return LeaseRenewal.objects.none()
        return LeaseRenewal.objects.filter(lease__organization=active_org)

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.status == LeaseRenewal.Status.APPROVED:
            self.object.approve(self.request.user)
        elif self.object.status == LeaseRenewal.Status.REJECTED:
            self.object.reject(self.request.user)
        return response
