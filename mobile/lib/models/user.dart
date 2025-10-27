/// User model for local storage and API communication.
///
/// Implements T040 from tasks.md.
library;

/// User role enum matching backend UserRole.
enum UserRole {
  owner('owner'),
  intermediary('intermediary'),
  tenant('tenant');

  const UserRole(this.value);
  final String value;

  static UserRole fromString(String value) {
    return UserRole.values.firstWhere(
      (role) => role.value == value,
      orElse: () => throw ArgumentError('Invalid user role: $value'),
    );
  }
}

/// User model with all fields from backend.
class User {
  final String id;
  final String email;
  final String fullName;
  final String? phone;
  final UserRole role;
  final bool isActive;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? lastLoginAt;

  User({
    required this.id,
    required this.email,
    required this.fullName,
    this.phone,
    required this.role,
    required this.isActive,
    required this.createdAt,
    required this.updatedAt,
    this.lastLoginAt,
  });

  /// Create User from JSON (API response).
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String,
      email: json['email'] as String,
      fullName: json['full_name'] as String,
      phone: json['phone'] as String?,
      role: UserRole.fromString(json['role'] as String),
      isActive: json['is_active'] as bool,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      lastLoginAt: json['last_login_at'] != null
          ? DateTime.parse(json['last_login_at'] as String)
          : null,
    );
  }

  /// Convert User to JSON for API requests.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'full_name': fullName,
      'phone': phone,
      'role': role.value,
      'is_active': isActive,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'last_login_at': lastLoginAt?.toIso8601String(),
    };
  }

  /// Create User from SQLite database row.
  factory User.fromMap(Map<String, dynamic> map) {
    return User(
      id: map['id'] as String,
      email: map['email'] as String,
      fullName: map['full_name'] as String,
      phone: map['phone'] as String?,
      role: UserRole.fromString(map['role'] as String),
      isActive: (map['is_active'] as int) == 1,
      createdAt: DateTime.parse(map['created_at'] as String),
      updatedAt: DateTime.parse(map['updated_at'] as String),
      lastLoginAt: map['last_login_at'] != null
          ? DateTime.parse(map['last_login_at'] as String)
          : null,
    );
  }

  /// Convert User to SQLite database row.
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'email': email,
      'full_name': fullName,
      'phone': phone,
      'role': role.value,
      'is_active': isActive ? 1 : 0,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'last_login_at': lastLoginAt?.toIso8601String(),
    };
  }

  /// Create a copy with updated fields.
  User copyWith({
    String? id,
    String? email,
    String? fullName,
    String? phone,
    UserRole? role,
    bool? isActive,
    DateTime? createdAt,
    DateTime? updatedAt,
    DateTime? lastLoginAt,
  }) {
    return User(
      id: id ?? this.id,
      email: email ?? this.email,
      fullName: fullName ?? this.fullName,
      phone: phone ?? this.phone,
      role: role ?? this.role,
      isActive: isActive ?? this.isActive,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      lastLoginAt: lastLoginAt ?? this.lastLoginAt,
    );
  }

  @override
  String toString() {
    return 'User(id: $id, email: $email, fullName: $fullName, role: ${role.value})';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;

    return other is User && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;
}
