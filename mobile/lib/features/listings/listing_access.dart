bool canManageListings(Iterable<String> roles) {
  return roles.any((role) {
    final normalized = role.toLowerCase();
    return normalized.contains('landlord') ||
        normalized.contains('owner') ||
        normalized.contains('admin');
  });
}
