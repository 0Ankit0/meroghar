from django.views.generic import ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from apps.operations.models import Notification
from django.utils import timezone

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'operations/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

class NotificationDetailView(LoginRequiredMixin, DetailView):
    model = Notification
    template_name = 'operations/notification_detail.html'
    context_object_name = 'notification'

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_read:
            obj.is_read = True
            obj.read_at = timezone.now()
            obj.save()
        return obj

class NotificationDeleteView(LoginRequiredMixin, DeleteView):
    model = Notification
    template_name = 'operations/notification_confirm_delete.html'
    success_url = reverse_lazy('operations:notification_list')

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
