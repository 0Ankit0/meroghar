from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission


class BaseOrgRolePermission(BasePermission):
    """
    Base permission that validates the active organization context and role.

    Tenants are restricted to object-level access to records tied to themselves.
    """

    allowed_roles: set[str] = set()
    owner_roles: set[str] = {"ADMIN"}

    org_paths = (
        "organization",
        "organizations",
        "property.organization",
        "unit.property.organization",
        "lead.organization",
        "lease.organization",
        "invoice.organization",
    )

    tenant_owner_paths = (
        "user",
        "tenant.user",
        "requester.user",
        "lease.tenant.user",
        "invoice.lease.tenant.user",
    )

    def has_permission(self, request, view):
        role = self._get_active_org_role(request)
        return bool(role and role in self.allowed_roles)

    def has_object_permission(self, request, view, obj):
        role = self._get_active_org_role(request)
        if not role or role not in self.allowed_roles:
            return False

        if not self._belongs_to_active_org(request, obj):
            return False

        if role in self.owner_roles or role in {"MANAGER", "STAFF", "VENDOR"}:
            return True

        # Tenant-level users can only access their own records.
        return self._is_tenant_owner(request.user, obj)

    def _get_active_org_role(self, request) -> str | None:
        user = getattr(request, "user", None)
        active_org = getattr(request, "active_organization", None)
        if not user or not user.is_authenticated or not active_org:
            return None
        if not user.organizations.filter(id=active_org.id).exists():
            return None
        return getattr(user, "role", None)

    def _belongs_to_active_org(self, request, obj: Any) -> bool:
        active_org = getattr(request, "active_organization", None)
        if not active_org:
            return False

        for path in self.org_paths:
            org = self._resolve_attr_path(obj, path)
            if org is not None:
                if hasattr(org, "filter"):
                    return org.filter(id=active_org.id).exists()
                return org == active_org

        return False

    def _is_tenant_owner(self, user, obj: Any) -> bool:
        for path in self.tenant_owner_paths:
            obj_user = self._resolve_attr_path(obj, path)
            if obj_user is not None:
                return obj_user == user
        return False

    @staticmethod
    def _resolve_attr_path(obj: Any, path: str) -> Any:
        current = obj
        for field in path.split("."):
            current = getattr(current, field, None)
            if current is None:
                return None
        return current


class IsOrgOwner(BaseOrgRolePermission):
    allowed_roles = {"ADMIN"}


class IsOrgManager(BaseOrgRolePermission):
    allowed_roles = {"ADMIN", "MANAGER"}


class IsOrgTenant(BaseOrgRolePermission):
    allowed_roles = {"ADMIN", "MANAGER", "STAFF", "VENDOR", "TENANT"}
