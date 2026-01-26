from apps.iam.models import Organization

class OrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Default
        request.active_organization = None
        
        if request.user.is_authenticated:
            active_org_id = request.session.get('active_org_id')
            
            if active_org_id:
                try:
                    # Check membership
                    org = request.user.organizations.get(id=active_org_id)
                    request.active_organization = org
                except Organization.DoesNotExist:
                    # Session org is invalid or user removed from it
                    active_org_id = None
            
            if not request.active_organization:
                # Fallback to first available
                first_org = request.user.organizations.first()
                if first_org:
                    request.active_organization = first_org
                    request.session['active_org_id'] = str(first_org.id)
        
        response = self.get_response(request)
        return response
