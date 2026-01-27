from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from ..models import Lead
from ..forms import LeadForm

class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = 'crm/lead_list.html'
    context_object_name = 'leads'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.active_organization:
            return qs.filter(organization=self.request.active_organization)
        return qs.none()

class LeadCreateView(LoginRequiredMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = 'crm/lead_form.html'
    success_url = reverse_lazy('crm:lead_list')

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        return super().form_valid(form)

class LeadUpdateView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = 'crm/lead_form.html'
    success_url = reverse_lazy('crm:lead_list')

    def get_queryset(self):
        if self.request.active_organization:
            return Lead.objects.filter(organization=self.request.active_organization)
        return Lead.objects.none()
