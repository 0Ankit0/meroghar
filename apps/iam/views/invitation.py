from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, View

from apps.iam.models import OrganizationInvitation, OrganizationMembership


class InvitationListView(LoginRequiredMixin, ListView):
    model = OrganizationInvitation
    template_name = 'iam/invitation_list.html'
    context_object_name = 'invitations'

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if not active_org:
            return OrganizationInvitation.objects.none()
        return OrganizationInvitation.objects.filter(organization=active_org).order_by('-created_at')


class InvitationCreateView(LoginRequiredMixin, CreateView):
    model = OrganizationInvitation
    fields = ['email', 'role', 'expires_at']
    template_name = 'iam/invitation_form.html'
    success_url = reverse_lazy('iam:invitation_list')

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.invited_by = self.request.user
        return super().form_valid(form)


class InvitationAcceptView(LoginRequiredMixin, View):
    def post(self, request, token):
        invitation = OrganizationInvitation.objects.filter(token=token).first()
        if invitation and invitation.status == OrganizationInvitation.Status.PENDING:
            OrganizationMembership.objects.update_or_create(
                organization=invitation.organization,
                user=request.user,
                defaults={'role': invitation.role, 'invited_by': invitation.invited_by, 'is_active': True},
            )
            request.user.organizations.add(invitation.organization)
            invitation.mark_accepted(request.user)
        return redirect('iam:organization_list')
