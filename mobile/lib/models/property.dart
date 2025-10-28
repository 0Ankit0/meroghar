/// Property model for local storage and API communication.
///
/// Implements T041 from tasks.md.
library;

/// Property model with all fields from backend.
class Property {
  Property({
    required this.id,
    required this.ownerId,
    required this.name,
    required this.addressLine1,
    this.addressLine2,
    required this.city,
    required this.state,
    required this.postalCode,
    required this.country,
    required this.totalUnits,
    required this.baseCurrency,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Create Property from JSON (API response).
  factory Property.fromJson(Map<String, dynamic> json) {
    return Property(
      id: json['id'] as String,
      ownerId: json['owner_id'] as String,
      name: json['name'] as String,
      addressLine1: json['address_line1'] as String,
      addressLine2: json['address_line2'] as String?,
      city: json['city'] as String,
      state: json['state'] as String,
      postalCode: json['postal_code'] as String,
      country: json['country'] as String,
      totalUnits: json['total_units'] as int,
      baseCurrency: json['base_currency'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  /// Create Property from SQLite database row.
  factory Property.fromMap(Map<String, dynamic> map) {
    return Property(
      id: map['id'] as String,
      ownerId: map['owner_id'] as String,
      name: map['name'] as String,
      addressLine1: map['address_line1'] as String,
      addressLine2: map['address_line2'] as String?,
      city: map['city'] as String,
      state: map['state'] as String,
      postalCode: map['postal_code'] as String,
      country: map['country'] as String,
      totalUnits: map['total_units'] as int,
      baseCurrency: map['base_currency'] as String,
      createdAt: DateTime.parse(map['created_at'] as String),
      updatedAt: DateTime.parse(map['updated_at'] as String),
    );
  }
  final String id;
  final String ownerId;
  final String name;
  final String addressLine1;
  final String? addressLine2;
  final String city;
  final String state;
  final String postalCode;
  final String country;
  final int totalUnits;
  final String baseCurrency;
  final DateTime createdAt;
  final DateTime updatedAt;

  /// Full address as a single string.
  String get fullAddress {
    final parts = [
      addressLine1,
      if (addressLine2 != null && addressLine2!.isNotEmpty) addressLine2,
      city,
      state,
      postalCode,
      country,
    ];
    return parts.join(', ');
  }

  /// Convert Property to JSON for API requests.
  Map<String, dynamic> toJson() => {
        'id': id,
        'owner_id': ownerId,
        'name': name,
        'address_line1': addressLine1,
        'address_line2': addressLine2,
        'city': city,
        'state': state,
        'postal_code': postalCode,
        'country': country,
        'total_units': totalUnits,
        'base_currency': baseCurrency,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
      };

  /// Convert Property to SQLite database row.
  Map<String, dynamic> toMap() => {
        'id': id,
        'owner_id': ownerId,
        'name': name,
        'address_line1': addressLine1,
        'address_line2': addressLine2,
        'city': city,
        'state': state,
        'postal_code': postalCode,
        'country': country,
        'total_units': totalUnits,
        'base_currency': baseCurrency,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
      };

  /// Create a copy with updated fields.
  Property copyWith({
    String? id,
    String? ownerId,
    String? name,
    String? addressLine1,
    String? addressLine2,
    String? city,
    String? state,
    String? postalCode,
    String? country,
    int? totalUnits,
    String? baseCurrency,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) =>
      Property(
        id: id ?? this.id,
        ownerId: ownerId ?? this.ownerId,
        name: name ?? this.name,
        addressLine1: addressLine1 ?? this.addressLine1,
        addressLine2: addressLine2 ?? this.addressLine2,
        city: city ?? this.city,
        state: state ?? this.state,
        postalCode: postalCode ?? this.postalCode,
        country: country ?? this.country,
        totalUnits: totalUnits ?? this.totalUnits,
        baseCurrency: baseCurrency ?? this.baseCurrency,
        createdAt: createdAt ?? this.createdAt,
        updatedAt: updatedAt ?? this.updatedAt,
      );

  @override
  String toString() =>
      'Property(id: $id, name: $name, city: $city, totalUnits: $totalUnits)';

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;

    return other is Property && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;
}
