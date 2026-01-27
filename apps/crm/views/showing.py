from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from ..models import Showing
from ..forms import ShowingForm

class ShowingListView(LoginRequiredMixin, ListView):
    model = Showing
    template_name = 'crm/showing_list.html'
    context_object_name = 'showings'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.active_organization:
            return qs.filter(lead__organization=self.request.active_organization)
        return qs.none()

class ShowingCreateView(LoginRequiredMixin, CreateView):
    model = Showing
    form_class = ShowingForm
    template_name = 'crm/showing_form.html'
    success_url = reverse_lazy('crm:showing_list')

    # Showing doesn't directly link to Org, but Lead and Unit do.
    # Form validation ensures linked Lead belongs to Org (ideally).
