import 'package:equatable/equatable.dart';

class CreateBookingRequest extends Equatable {
  final String propertyId;
  final DateTime rentalStartAt;
  final DateTime rentalEndAt;
  final String? specialRequests;
  final String? paymentMethodId;
  final String? idempotencyKey;

  const CreateBookingRequest({
    required this.propertyId,
    required this.rentalStartAt,
    required this.rentalEndAt,
    this.specialRequests,
    this.paymentMethodId,
    this.idempotencyKey,
  });

  Map<String, dynamic> toJson() {
    return {
      'propertyId': propertyId,
      'rentalStartAt': rentalStartAt.toUtc().toIso8601String(),
      'rentalEndAt': rentalEndAt.toUtc().toIso8601String(),
      if (specialRequests != null && specialRequests!.trim().isNotEmpty)
        'specialRequests': specialRequests!.trim(),
      if (paymentMethodId != null && paymentMethodId!.trim().isNotEmpty)
        'paymentMethodId': paymentMethodId!.trim(),
    };
  }

  Map<String, String> toHeaders() {
    if (idempotencyKey == null || idempotencyKey!.trim().isEmpty) {
      return const <String, String>{};
    }
    return {'Idempotency-Key': idempotencyKey!.trim()};
  }

  @override
  List<Object?> get props => [
        propertyId,
        rentalStartAt,
        rentalEndAt,
        specialRequests,
        paymentMethodId,
        idempotencyKey,
      ];
}
