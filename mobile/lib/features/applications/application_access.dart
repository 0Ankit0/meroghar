bool _containsAny(String value, Iterable<String> fragments) {
  return fragments.any(value.contains);
}

List<String> _normalizeRoles(Iterable<String> roles) {
  return roles
      .map((role) => role.trim().toLowerCase())
      .where((role) => role.isNotEmpty)
      .toList();
}

bool canViewApplications(Iterable<String> roles) {
  final normalized = _normalizeRoles(roles);
  if (normalized.isEmpty) return true;
  return normalized.any((role) => _containsAny(
        role,
        const ['tenant', 'customer', 'renter'],
      ));
}

bool canSubmitApplications(Iterable<String> roles) {
  final normalized = _normalizeRoles(roles);
  if (normalized.isEmpty) return true;
  return normalized.any((role) => _containsAny(
        role,
        const ['tenant', 'customer', 'renter'],
      ));
}

bool canManageApplications(Iterable<String> _) {
  return false;
}

bool canManageAgreements(Iterable<String> _) {
  return false;
}

bool canSignLeaseAgreement(Iterable<String> roles) {
  return canSubmitApplications(roles);
}
