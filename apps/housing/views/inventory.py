from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from ..models import InventoryItem
from ..forms import InventoryItemForm

class InventoryListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    template_name = 'housing/inventory_list.html'
    context_object_name = 'items'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.active_organization:
            return qs.filter(unit__property__organization=self.request.active_organization)
        return qs.none()

class InventoryCreateView(LoginRequiredMixin, CreateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'housing/inventory_form.html'
    success_url = reverse_lazy('housing:inventory_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.active_organization
        return kwargs

class InventoryUpdateView(LoginRequiredMixin, UpdateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'housing/inventory_form.html'
    success_url = reverse_lazy('housing:inventory_list')

    def get_form_kwargs(self):
         kwargs = super().get_form_kwargs()
         kwargs['organization'] = self.request.active_organization
         return kwargs

    def get_queryset(self):
        if self.request.active_organization:
             return InventoryItem.objects.filter(unit__property__organization=self.request.active_organization)
        return InventoryItem.objects.none()
