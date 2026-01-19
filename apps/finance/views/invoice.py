from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from ..models import Invoice
from apps.iam.models import Organization

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = "finance/invoice_list.html"
    context_object_name = "invoices"

class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = "finance/invoice_detail.html"
    context_object_name = "invoice"
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Invoice.objects.filter(organization=user.organization)
        return Invoice.objects.none()

class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    fields = ['lease', 'invoice_number', 'invoice_date', 'due_date', 'total_amount', 'status']
    template_name = "finance/invoice_form.html"
    success_url = reverse_lazy('finance:invoice_list')

    def form_valid(self, form):
        user = self.request.user
        if not user.organization:
            org_name = f"{user.get_full_name() or user.username}'s Properties"
            org = Organization.objects.create(name=org_name)
            user.organization = org
            user.save()
        
        form.instance.organization = user.organization
        return super().form_valid(form)

class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    fields = ['lease', 'invoice_number', 'invoice_date', 'due_date', 'total_amount', 'status']
    template_name = "finance/invoice_form.html"
    success_url = reverse_lazy('finance:invoice_list')
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Invoice.objects.filter(organization=user.organization)
        return Invoice.objects.none()

class InvoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Invoice
    template_name = "finance/invoice_confirm_delete.html"
    success_url = reverse_lazy('finance:invoice_list')
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Invoice.objects.filter(organization=user.organization)
        return Invoice.objects.none()
