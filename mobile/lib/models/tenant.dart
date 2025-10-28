/// Tenant model for local storage and API communication.
///
/// Implements T042 from tasks.md.
library;

/// Tenant status enum matching backend TenantStatus.
enum TenantStatus {
  active('active'),
  movedOut('moved_out');

  const TenantStatus(this.value);
  final String value;

  static TenantStatus fromString(String value) =>
      TenantStatus.values.firstWhere(
        (status) => status.value == value,
        orElse: () => throw ArgumentError('Invalid tenant status: $value'),
      );
}

/// Tenant model with all fields from backend.
class Tenant {
  Tenant({
    required this.id,
    required this.userId,
    required this.propertyId,
    required this.moveInDate,
    this.moveOutDate,
    required this.monthlyRent,
    required this.securityDeposit,
    required this.electricityRate,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Create Tenant from JSON (API response).
  factory Tenant.fromJson(Map<String, dynamic> json) => Tenant(
        id: json['id'] as String,
        userId: json['user_id'] as String,
        propertyId: json['property_id'] as String,
        moveInDate: DateTime.parse(json['move_in_date'] as String),
        moveOutDate: json['move_out_date'] != null
            ? DateTime.parse(json['move_out_date'] as String)
            : null,
        monthlyRent: (json['monthly_rent'] as num).toDouble(),
        securityDeposit: (json['security_deposit'] as num).toDouble(),
        electricityRate: (json['electricity_rate'] as num).toDouble(),
        status: TenantStatus.fromString(json['status'] as String),
        createdAt: DateTime.parse(json['created_at'] as String),
        updatedAt: DateTime.parse(json['updated_at'] as String),
      );

  /// Create Tenant from SQLite database row.
  factory Tenant.fromMap(Map<String, dynamic> map) => Tenant(
        id: map['id'] as String,
        userId: map['user_id'] as String,
        propertyId: map['property_id'] as String,
        moveInDate: DateTime.parse(map['move_in_date'] as String),
        moveOutDate: map['move_out_date'] != null
            ? DateTime.parse(map['move_out_date'] as String)
            : null,
        monthlyRent: (map['monthly_rent'] as num).toDouble(),
        securityDeposit: (map['security_deposit'] as num).toDouble(),
        electricityRate: (map['electricity_rate'] as num).toDouble(),
        status: TenantStatus.fromString(map['status'] as String),
        createdAt: DateTime.parse(map['created_at'] as String),
        updatedAt: DateTime.parse(map['updated_at'] as String),
      );
  final String id;
  final String userId;
  final String propertyId;
  final DateTime moveInDate;
  final DateTime? moveOutDate;
  final double monthlyRent;
  final double securityDeposit;
  final double electricityRate;
  final TenantStatus status;
  final DateTime createdAt;
  final DateTime updatedAt;

  /// Calculate months stayed (including partial months).
  int get monthsStayed {
    final endDate = moveOutDate ?? DateTime.now();
    final difference = endDate.difference(moveInDate);
    return (difference.inDays / 30).ceil();
  }

  /// Check if tenant is currently active.
  bool get isActive => status == TenantStatus.active && moveOutDate == null;

  /// Convert Tenant to JSON for API requests.
  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'property_id': propertyId,
        'move_in_date': moveInDate.toIso8601String().split('T')[0], // Date only
        'move_out_date': moveOutDate?.toIso8601String().split('T')[0],
        'monthly_rent': monthlyRent,
        'security_deposit': securityDeposit,
        'electricity_rate': electricityRate,
        'status': status.value,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
      };

  /// Convert Tenant to SQLite database row.
  Map<String, dynamic> toMap() => {
        'id': id,
        'user_id': userId,
        'property_id': propertyId,
        'move_in_date': moveInDate.toIso8601String(),
        'move_out_date': moveOutDate?.toIso8601String(),
        'monthly_rent': monthlyRent,
        'security_deposit': securityDeposit,
        'electricity_rate': electricityRate,
        'status': status.value,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
      };

  /// Create a copy with updated fields.
  Tenant copyWith({
    String? id,
    String? userId,
    String? propertyId,
    DateTime? moveInDate,
    DateTime? moveOutDate,
    double? monthlyRent,
    double? securityDeposit,
    double? electricityRate,
    TenantStatus? status,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) =>
      Tenant(
        id: id ?? this.id,
        userId: userId ?? this.userId,
        propertyId: propertyId ?? this.propertyId,
        moveInDate: moveInDate ?? this.moveInDate,
        moveOutDate: moveOutDate ?? this.moveOutDate,
        monthlyRent: monthlyRent ?? this.monthlyRent,
        securityDeposit: securityDeposit ?? this.securityDeposit,
        electricityRate: electricityRate ?? this.electricityRate,
        status: status ?? this.status,
        createdAt: createdAt ?? this.createdAt,
        updatedAt: updatedAt ?? this.updatedAt,
      );

  @override
  String toString() =>
      'Tenant(id: $id, userId: $userId, propertyId: $propertyId, status: ${status.value})';

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;

    return other is Tenant && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;
}
