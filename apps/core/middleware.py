from apps.core.organization import resolve_active_organization

class OrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Default
        request.active_organization = None
        request.active_organization = resolve_active_organization(request, request.user)
        
        response = self.get_response(request)
        return response
