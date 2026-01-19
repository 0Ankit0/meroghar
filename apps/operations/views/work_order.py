from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import WorkOrder
from apps.iam.models import Organization

class WorkOrderListView(LoginRequiredMixin, ListView):
    model = WorkOrder
    template_name = "operations/work_order_list.html"
    context_object_name = "work_orders"
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return WorkOrder.objects.filter(organization=user.organization)
        return WorkOrder.objects.none()

class WorkOrderCreateView(LoginRequiredMixin, CreateView):
    model = WorkOrder
    fields = ['unit', 'requester', 'title', 'description', 'priority']
    template_name = "operations/work_order_form.html"
    success_url = reverse_lazy('operations:work_order_list')

    def form_valid(self, form):
        user = self.request.user
        if not user.organization:
            org_name = f"{user.get_full_name() or user.username}'s Properties"
            org = Organization.objects.create(name=org_name)
            user.organization = org
            user.save()
        
        form.instance.organization = user.organization
        return super().form_valid(form)

class WorkOrderDetailView(LoginRequiredMixin, DetailView):
    model = WorkOrder
    template_name = "operations/work_order_detail.html"
    context_object_name = "work_order"
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return WorkOrder.objects.filter(organization=user.organization)
        return WorkOrder.objects.none()

class WorkOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = WorkOrder
    fields = ['unit', 'requester', 'title', 'description', 'priority', 'status', 'assigned_to']
    template_name = "operations/work_order_form.html"
    success_url = reverse_lazy('operations:work_order_list')
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return WorkOrder.objects.filter(organization=user.organization)
        return WorkOrder.objects.none()

class WorkOrderDeleteView(LoginRequiredMixin, DeleteView):
    model = WorkOrder
    template_name = "operations/work_order_confirm_delete.html"
    success_url = reverse_lazy('operations:work_order_list')
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return WorkOrder.objects.filter(organization=user.organization)
        return WorkOrder.objects.none()
