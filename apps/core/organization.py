from __future__ import annotations

from typing import Optional

from apps.iam.models import Organization


ORGANIZATION_HEADER = "HTTP_X_ORGANIZATION_ID"


def resolve_active_organization(request, user) -> Optional[Organization]:
    """
    Resolve an active organization for authenticated users.

    Priority:
    1. X-Organization-ID request header (validated against membership).
    2. Session active_org_id (validated against membership).
    3. First available user organization.
    """
    if not user or not user.is_authenticated:
        return None

    request.organization_header_invalid = False
    request.organization_header_value = None

    header_org_id = request.META.get(ORGANIZATION_HEADER)
    if header_org_id:
        request.organization_header_value = header_org_id
        try:
            org = user.organizations.get(id=header_org_id)
            request.session["active_org_id"] = str(org.id)
            return org
        except (Organization.DoesNotExist, ValueError, TypeError):
            request.organization_header_invalid = True
            return None

    session_org_id = request.session.get("active_org_id")
    if session_org_id:
        try:
            return user.organizations.get(id=session_org_id)
        except (Organization.DoesNotExist, ValueError, TypeError):
            request.session.pop("active_org_id", None)

    fallback_org = user.organizations.first()
    if fallback_org:
        request.session["active_org_id"] = str(fallback_org.id)
    return fallback_org
