from django.http import JsonResponse

from apps.iam.models import Organization, User



class OrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.active_organization = None

        if request.user.is_authenticated:
            active_org_id = request.session.get('active_org_id')

            if active_org_id:
                try:
                    org = request.user.organizations.get(id=active_org_id)
                    request.active_organization = org
                except Organization.DoesNotExist:
                    active_org_id = None

            if not request.active_organization:
                first_org = request.user.organizations.first()
                if first_org:
                    request.active_organization = first_org
                    request.session['active_org_id'] = str(first_org.id)

        response = self.get_response(request)
        return response


class AccessVerificationMiddleware:
    EXEMPT_PATH_PREFIXES = (
        '/admin/login/',
        '/accounts/login/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and isinstance(user, User):
            if not user.can_access_platform() and not any(request.path.startswith(prefix) for prefix in self.EXEMPT_PATH_PREFIXES):
                if request.path.startswith('/api/'):
                    return JsonResponse({'detail': 'Account is not verified yet.'}, status=403)
                return JsonResponse({'detail': 'Account is not verified yet.'}, status=403)

        return self.get_response(request)
