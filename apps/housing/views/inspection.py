from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from ..models import PropertyInspection
from ..forms import PropertyInspectionForm

class InspectionListView(LoginRequiredMixin, ListView):
    model = PropertyInspection
    template_name = 'housing/inspection_list.html'
    context_object_name = 'inspections'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.active_organization:
            return qs.filter(unit__property__organization=self.request.active_organization)
        return qs.none()

class InspectionCreateView(LoginRequiredMixin, CreateView):
    model = PropertyInspection
    form_class = PropertyInspectionForm
    template_name = 'housing/inspection_form.html'
    success_url = reverse_lazy('housing:inspection_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.active_organization
        return kwargs

class InspectionUpdateView(LoginRequiredMixin, UpdateView):
    model = PropertyInspection
    form_class = PropertyInspectionForm
    template_name = 'housing/inspection_form.html'
    success_url = reverse_lazy('housing:inspection_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.active_organization
        return kwargs
    
    def get_queryset(self):
        if self.request.active_organization:
            return PropertyInspection.objects.filter(unit__property__organization=self.request.active_organization)
        return PropertyInspection.objects.none()
