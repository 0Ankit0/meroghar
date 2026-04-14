import 'package:equatable/equatable.dart';

class CreateListingRequest extends Equatable {
  final String propertyTypeId;
  final String name;
  final String description;
  final String locationAddress;
  final double? depositAmount;
  final int? minRentalDurationHours;
  final int? maxRentalDurationDays;
  final bool instantBookingEnabled;
  final Map<String, dynamic> attributes;

  const CreateListingRequest({
    required this.propertyTypeId,
    required this.name,
    required this.description,
    required this.locationAddress,
    this.depositAmount,
    this.minRentalDurationHours,
    this.maxRentalDurationDays,
    this.instantBookingEnabled = false,
    this.attributes = const {},
  });

  Map<String, dynamic> toJson() {
    final payload = <String, dynamic>{
      'property_type_id': propertyTypeId,
      'name': name,
      'description': description,
      'location_address': locationAddress,
      'instant_booking_enabled': instantBookingEnabled,
    };

    if (depositAmount != null) {
      payload['deposit_amount'] = depositAmount;
    }
    if (minRentalDurationHours != null) {
      payload['min_rental_duration_hours'] = minRentalDurationHours;
    }
    if (maxRentalDurationDays != null) {
      payload['max_rental_duration_days'] = maxRentalDurationDays;
    }
    if (attributes.isNotEmpty) {
      payload['attributes'] = attributes;
    }

    return payload;
  }

  @override
  List<Object?> get props => [
        propertyTypeId,
        name,
        description,
        locationAddress,
        depositAmount,
        minRentalDurationHours,
        maxRentalDurationDays,
        instantBookingEnabled,
        attributes,
      ];
}
