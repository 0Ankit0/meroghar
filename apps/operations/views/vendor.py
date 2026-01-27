from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from ..models import Vendor
from ..forms import VendorForm

class VendorListView(LoginRequiredMixin, ListView):
    model = Vendor
    template_name = 'operations/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.active_organization:
            return qs.filter(organization=self.request.active_organization)
        return qs.none()

class VendorCreateView(LoginRequiredMixin, CreateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'operations/vendor_form.html'
    success_url = reverse_lazy('operations:vendor_list')

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        return super().form_valid(form)

class VendorUpdateView(LoginRequiredMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'operations/vendor_form.html'
    success_url = reverse_lazy('operations:vendor_list')

    def get_queryset(self):
        if self.request.active_organization:
            return Vendor.objects.filter(organization=self.request.active_organization)
        return Vendor.objects.none()
