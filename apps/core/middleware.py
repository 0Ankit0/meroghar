from apps.iam.models import Organization


class OrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.active_organization = None

        if request.user.is_authenticated:
            active_org_id = request.session.get('active_org_id')

            if active_org_id:
                org = Organization.objects.filter(
                    id=active_org_id,
                    memberships__user=request.user,
                    memberships__is_active=True,
                ).first()
                if org:
                    request.active_organization = org

            if not request.active_organization:
                first_org = Organization.objects.filter(
                    memberships__user=request.user,
                    memberships__is_active=True,
                ).order_by('name').first()
                if first_org:
                    request.active_organization = first_org
                    request.session['active_org_id'] = str(first_org.id)

        return self.get_response(request)
