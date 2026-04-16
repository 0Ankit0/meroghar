bool _containsAny(String value, Iterable<String> fragments) {
  return fragments.any(value.contains);
}

List<String> _normalizeRoles(Iterable<String> roles) {
  return roles
      .map((role) => role.trim().toLowerCase())
      .where((role) => role.isNotEmpty)
      .toList();
}

bool canViewTenantBilling(Iterable<String> roles) {
  final normalized = _normalizeRoles(roles);
  if (normalized.isEmpty) return true;
  return normalized.any((role) => _containsAny(
        role,
        const ['tenant', 'customer', 'renter'],
      ));
}

bool shouldUseWebsiteForBillingManagement(Iterable<String> roles) {
  final normalized = _normalizeRoles(roles);
  if (normalized.isEmpty) return false;
  return normalized.any((role) => _containsAny(
        role,
        const ['owner', 'landlord', 'manager', 'admin', 'staff'],
      ));
}
