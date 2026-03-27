from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import WorkOrder
from apps.iam.models import Organization, OrganizationMembership

class WorkOrderListView(LoginRequiredMixin, ListView):
    model = WorkOrder
    template_name = "operations/work_order_list.html"
    context_object_name = "work_orders"
    
    def get_queryset(self):
        if self.request.active_organization:
             return WorkOrder.objects.filter(organization=self.request.active_organization)
        return WorkOrder.objects.none()

class WorkOrderCreateView(LoginRequiredMixin, CreateView):
    model = WorkOrder
    fields = ['unit', 'requester', 'title', 'description', 'priority', 'preferred_service_type', 'actual_hours']
    template_name = "operations/work_order_form.html"
    success_url = reverse_lazy('operations:work_order_list')

    def form_valid(self, form):
        user = self.request.user
        
        # Ensure active org
        if not self.request.active_organization:
             # Create default
             org_name = f"{user.get_full_name() or user.username}'s Properties"
             org = Organization.objects.create(name=org_name)
             OrganizationMembership.objects.get_or_create(
                organization=org,
                user=user,
                defaults={'role': OrganizationMembership.Role.OWNER, 'invited_by': user},
            )
             self.request.active_organization = org
             self.request.session['active_org_id'] = str(org.id)
        
        form.instance.organization = self.request.active_organization
        return super().form_valid(form)

class WorkOrderDetailView(LoginRequiredMixin, DetailView):
    model = WorkOrder
    template_name = "operations/work_order_detail.html"
    context_object_name = "work_order"
    
    def get_queryset(self):
        if self.request.active_organization:
            return WorkOrder.objects.filter(organization=self.request.active_organization)
        return WorkOrder.objects.none()

class WorkOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = WorkOrder
    fields = [
        'unit',
        'requester',
        'title',
        'description',
        'priority',
        'preferred_service_type',
        'status',
        'assigned_to',
        'assigned_vendor',
        'actual_hours',
    ]
    template_name = "operations/work_order_form.html"
    success_url = reverse_lazy('operations:work_order_list')
    
    def get_queryset(self):
        if self.request.active_organization:
            return WorkOrder.objects.filter(organization=self.request.active_organization)
        return WorkOrder.objects.none()

class WorkOrderDeleteView(LoginRequiredMixin, DeleteView):
    model = WorkOrder
    template_name = "operations/work_order_confirm_delete.html"
    success_url = reverse_lazy('operations:work_order_list')
    
    def get_queryset(self):
        if self.request.active_organization:
            return WorkOrder.objects.filter(organization=self.request.active_organization)
        return WorkOrder.objects.none()
