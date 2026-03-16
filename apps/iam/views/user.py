from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from apps.iam.models import User, OrganizationMembership


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
            return True
        active_org = getattr(self.request, 'active_organization', None)
        return self.request.user.has_org_role(
            active_org,
            {OrganizationMembership.Role.OWNER, OrganizationMembership.Role.ADMIN},
        )


class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = "iam/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if not active_org:
            return User.objects.none()
        return User.objects.filter(
            organization_memberships__organization=active_org,
            organization_memberships__is_active=True,
        ).distinct().order_by('-date_joined')


class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name', 'role', 'password']
    template_name = "iam/user_form.html"
    success_url = reverse_lazy('iam:user_list')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.set_password(form.cleaned_data['password'])
        self.object.save()
        active_org = getattr(self.request, 'active_organization', None)
        if active_org:
            OrganizationMembership.objects.update_or_create(
                organization=active_org,
                user=self.object,
                defaults={
                    'role': form.cleaned_data['role'],
                    'is_active': True,
                    'invited_by': self.request.user,
                },
            )
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(self.get_success_url())


class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    template_name = "iam/user_form.html"
    success_url = reverse_lazy('iam:user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        active_org = getattr(self.request, 'active_organization', None)
        if active_org:
            OrganizationMembership.objects.update_or_create(
                organization=active_org,
                user=self.object,
                defaults={
                    'role': form.cleaned_data['role'],
                    'is_active': form.cleaned_data['is_active'],
                    'invited_by': self.request.user,
                },
            )
        return response


class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = "iam/user_confirm_delete.html"
    success_url = reverse_lazy('iam:user_list')
