from apps.core.organization import resolve_active_organization

class OrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.active_organization = None
        request.active_organization = resolve_active_organization(request, request.user)
        
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
