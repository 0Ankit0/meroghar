from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from apps.core.organization import resolve_active_organization


class OrganizationAwareSessionAuthentication(SessionAuthentication):
    def authenticate(self, request):
        auth_result = super().authenticate(request)
        if auth_result:
            user, _ = auth_result
            request._request.active_organization = resolve_active_organization(request._request, user)
        return auth_result


class OrganizationAwareTokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        auth_result = super().authenticate(request)
        if auth_result:
            user, _ = auth_result
            request._request.active_organization = resolve_active_organization(request._request, user)
        return auth_result

