from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

from apps.crm.models import LeadFollowUp


class FollowUpListView(LoginRequiredMixin, ListView):
    model = LeadFollowUp
    template_name = 'crm/followup_list.html'
    context_object_name = 'followups'

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if not active_org:
            return LeadFollowUp.objects.none()
        return LeadFollowUp.objects.filter(lead__organization=active_org).order_by('scheduled_at')


class FollowUpCreateView(LoginRequiredMixin, CreateView):
    model = LeadFollowUp
    fields = ['lead', 'channel', 'scheduled_at', 'status', 'message']
    template_name = 'crm/followup_form.html'
    success_url = reverse_lazy('crm:followup_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        active_org = getattr(self.request, 'active_organization', None)
        if active_org:
            form.fields['lead'].queryset = form.fields['lead'].queryset.filter(organization=active_org)
        return form
