import 'package:equatable/equatable.dart';
import '../../../../core/utils/json_parsing.dart';

String _normalizeToken(String value) {
  return value
      .trim()
      .toUpperCase()
      .replaceAll(RegExp(r'[.\s-]+'), '_')
      .replaceAll(RegExp(r'_+'), '_');
}

String normalizeBookingStatus(String value) {
  final normalized = _normalizeToken(value);
  switch (normalized) {
    case 'APPROVED':
    case 'AUTO_CONFIRMED':
      return 'CONFIRMED';
    case 'RETURN_PENDING':
    case 'PENDING_RETURN':
      return 'PENDING_CLOSURE';
    default:
      return normalized.isEmpty ? 'PENDING' : normalized;
  }
}

String? normalizeAgreementStatusValue(String? value) {
  if (value == null || value.trim().isEmpty) return null;
  final normalized = _normalizeToken(value);
  switch (normalized) {
    case 'PENDING_TENANT_SIGNATURE':
      return 'PENDING_CUSTOMER_SIGNATURE';
    case 'PENDING_LANDLORD_SIGNATURE':
      return 'PENDING_OWNER_SIGNATURE';
    default:
      return normalized;
  }
}

class BookingPropertyRef extends Equatable {
  final String id;
  final String name;
  final String locationAddress;
  final String? coverImageUrl;

  const BookingPropertyRef({
    required this.id,
    required this.name,
    required this.locationAddress,
    this.coverImageUrl,
  });

  factory BookingPropertyRef.fromJson(Map<String, dynamic> json) {
    final photos = readList(json, ['photos', 'images', 'media']);
    return BookingPropertyRef(
      id: readString(json, ['id', 'property_id', 'listing_id', 'asset_id']) ??
          '',
      name: readString(json, ['name', 'title']) ?? 'Property',
      locationAddress: readString(
            json,
            ['location_address', 'address', 'location', 'city'],
          ) ??
          '',
      coverImageUrl: readString(json, [
            'cover_image_url',
            'coverImageUrl',
            'thumbnail_url',
            'image_url',
            'url',
          ]) ??
          _extractFirstImageUrl(photos),
    );
  }

  @override
  List<Object?> get props => [id, name, locationAddress, coverImageUrl];
}

String? _extractFirstImageUrl(List<dynamic> rawPhotos) {
  for (final rawPhoto in rawPhotos) {
    if (rawPhoto is String && rawPhoto.trim().isNotEmpty) {
      return rawPhoto.trim();
    }
    final photo = asJsonMap(rawPhoto);
    final url = readString(photo, [
      'thumbnail_url',
      'url',
      'image_url',
      'src',
    ]);
    if (url != null) return url;
  }
  return null;
}

class BookingPartyRef extends Equatable {
  final String id;
  final String name;
  final String? email;
  final String? phone;

  const BookingPartyRef({
    required this.id,
    required this.name,
    this.email,
    this.phone,
  });

  factory BookingPartyRef.fromJson(Map<String, dynamic> json) {
    final displayName = readString(
          json,
          ['display_name', 'name', 'full_name', 'username'],
        ) ??
        [
          readString(json, ['first_name']),
          readString(json, ['last_name']),
        ].whereType<String>().where((value) => value.isNotEmpty).join(' ').trim();

    return BookingPartyRef(
      id: readString(json, ['id', 'user_id', 'tenant_user_id', 'owner_user_id']) ??
          '',
      name: displayName.isNotEmpty ? displayName : 'Unknown user',
      email: readString(json, ['email']),
      phone: readString(json, ['phone', 'phone_number']),
    );
  }

  factory BookingPartyRef.fromDynamic(dynamic raw) {
    if (raw is String && raw.trim().isNotEmpty) {
      return BookingPartyRef(id: '', name: raw.trim());
    }
    final json = asJsonMap(raw);
    if (json.isEmpty) {
      return const BookingPartyRef(id: '', name: 'Unknown user');
    }
    return BookingPartyRef.fromJson(json);
  }

  String get subtitle {
    return [email, phone]
        .whereType<String>()
        .map((value) => value.trim())
        .where((value) => value.isNotEmpty)
        .join(' • ');
  }

  @override
  List<Object?> get props => [id, name, email, phone];
}

class BookingPricingItem extends Equatable {
  final String label;
  final double amount;
  final String? description;

  const BookingPricingItem({
    required this.label,
    required this.amount,
    this.description,
  });

  factory BookingPricingItem.fromJson(Map<String, dynamic> json) {
    return BookingPricingItem(
      label: readString(json, ['label', 'name', 'title', 'type']) ?? 'Charge',
      amount: readDouble(json, ['amount', 'value', 'total']) ?? 0,
      description: readString(json, ['description', 'detail']),
    );
  }

  @override
  List<Object?> get props => [label, amount, description];
}

class BookingPricing extends Equatable {
  final String currency;
  final double baseFee;
  final double peakSurcharge;
  final double taxAmount;
  final double totalFee;
  final double depositAmount;
  final double totalDueNow;
  final List<BookingPricingItem> lineItems;

  const BookingPricing({
    required this.currency,
    required this.baseFee,
    required this.peakSurcharge,
    required this.taxAmount,
    required this.totalFee,
    required this.depositAmount,
    required this.totalDueNow,
    this.lineItems = const [],
  });

  factory BookingPricing.fromJson(Map<String, dynamic> json) {
    final pricing = readMap(json, ['pricing', 'quote', 'pricing_breakdown']);
    final source = pricing.isNotEmpty ? pricing : json;
    final baseFee = readDouble(source,
            ['base_fee', 'base', 'monthly_rent', 'base_rental_fee', 'rent']) ??
        0;
    final peakSurcharge =
        readDouble(source, ['peak_surcharge', 'seasonal_surcharge']) ?? 0;
    final taxAmount = readDouble(source, ['tax_amount', 'tax']) ?? 0;
    final totalFee = readDouble(
          source,
          ['total_fee', 'quote_total', 'total', 'subtotal'],
        ) ??
        (baseFee + peakSurcharge + taxAmount);
    final depositAmount =
        readDouble(source, ['deposit_amount', 'security_deposit', 'deposit']) ??
            0;
    final totalDueNow = readDouble(
          source,
          ['total_due_now', 'due_now', 'payable_now'],
        ) ??
        (totalFee + depositAmount);
    final rawLineItems = readList(source, ['line_items', 'breakdown', 'items']);
    final lineItems = rawLineItems
        .map((item) => BookingPricingItem.fromJson(asJsonMap(item)))
        .where((item) => item.amount != 0)
        .toList();

    return BookingPricing(
      currency: readString(source, ['currency']) ??
          readString(json, ['currency']) ??
          'NPR',
      baseFee: baseFee,
      peakSurcharge: peakSurcharge,
      taxAmount: taxAmount,
      totalFee: totalFee,
      depositAmount: depositAmount,
      totalDueNow: totalDueNow,
      lineItems: lineItems.isNotEmpty
          ? lineItems
          : [
              if (baseFee != 0)
                BookingPricingItem(label: 'Base rent', amount: baseFee),
              if (peakSurcharge != 0)
                BookingPricingItem(
                  label: 'Peak surcharge',
                  amount: peakSurcharge,
                ),
              if (taxAmount != 0)
                BookingPricingItem(label: 'Tax', amount: taxAmount),
              if (depositAmount != 0)
                BookingPricingItem(
                  label: 'Security deposit',
                  amount: depositAmount,
                ),
            ],
    );
  }

  @override
  List<Object?> get props => [
        currency,
        baseFee,
        peakSurcharge,
        taxAmount,
        totalFee,
        depositAmount,
        totalDueNow,
        lineItems,
      ];
}

class BookingRecord extends Equatable {
  final String id;
  final String bookingNumber;
  final String status;
  final BookingPropertyRef property;
  final BookingPartyRef? tenant;
  final BookingPartyRef? landlord;
  final DateTime? rentalStartAt;
  final DateTime? rentalEndAt;
  final DateTime? actualReturnAt;
  final DateTime? holdExpiresAt;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final DateTime? confirmedAt;
  final DateTime? declinedAt;
  final DateTime? cancelledAt;
  final DateTime? activeAt;
  final DateTime? pendingClosureAt;
  final DateTime? closedAt;
  final String? specialRequests;
  final String? cancellationReason;
  final String? declineReason;
  final bool instantBookingEnabled;
  final String? agreementStatus;
  final BookingPricing pricing;

  const BookingRecord({
    required this.id,
    required this.bookingNumber,
    required this.status,
    required this.property,
    required this.pricing,
    this.tenant,
    this.landlord,
    this.rentalStartAt,
    this.rentalEndAt,
    this.actualReturnAt,
    this.holdExpiresAt,
    this.createdAt,
    this.updatedAt,
    this.confirmedAt,
    this.declinedAt,
    this.cancelledAt,
    this.activeAt,
    this.pendingClosureAt,
    this.closedAt,
    this.specialRequests,
    this.cancellationReason,
    this.declineReason,
    this.instantBookingEnabled = false,
    this.agreementStatus,
  });

  factory BookingRecord.fromJson(Map<String, dynamic> json) {
    final propertyMap = readMap(json, ['property', 'listing', 'asset']);
    final agreementMap = readMap(json, ['agreement', 'lease', 'rental_agreement']);

    final effectiveProperty = propertyMap.isNotEmpty
        ? propertyMap
        : {
            if (readString(json, ['propertyId', 'property_id']) != null)
              'id': readString(json, ['propertyId', 'property_id']),
            if (readString(json, ['propertyName', 'property_name']) != null)
              'name': readString(json, ['propertyName', 'property_name']),
            if (readString(json, ['location_address', 'address']) != null)
              'location_address': readString(
                json,
                ['location_address', 'address'],
              ),
          };

    final tenantMap = readMap(json, ['tenant', 'customer', 'applicant']);
    final landlordMap = readMap(json, ['owner', 'landlord']);

    return BookingRecord(
      id: readString(json, ['bookingId', 'booking_id', 'id']) ?? '',
      bookingNumber: readString(
            json,
            ['bookingNumber', 'booking_number', 'reference', 'code'],
          ) ??
          '',
      status: normalizeBookingStatus(
        readString(json, ['status', 'booking_status', 'application_status']) ??
            'PENDING',
      ),
      property: BookingPropertyRef.fromJson(asJsonMap(effectiveProperty)),
      tenant: tenantMap.isNotEmpty ? BookingPartyRef.fromJson(tenantMap) : null,
      landlord:
          landlordMap.isNotEmpty ? BookingPartyRef.fromJson(landlordMap) : null,
      rentalStartAt: readDateTime(
        json,
        ['rentalStartAt', 'rental_start_at', 'startAt', 'start_at'],
      ),
      rentalEndAt: readDateTime(
        json,
        ['rentalEndAt', 'rental_end_at', 'endAt', 'end_at'],
      ),
      actualReturnAt: readDateTime(
        json,
        ['actualReturnAt', 'actual_return_at', 'returnedAt', 'returned_at'],
      ),
      holdExpiresAt: readDateTime(
        json,
        ['holdExpiresAt', 'hold_expires_at', 'expiresAt', 'expires_at'],
      ),
      createdAt: readDateTime(
        json,
        ['createdAt', 'created_at', 'submittedAt', 'submitted_at'],
      ),
      updatedAt: readDateTime(json, ['updatedAt', 'updated_at']),
      confirmedAt: readDateTime(
        json,
        ['confirmedAt', 'confirmed_at', 'approvedAt', 'approved_at'],
      ),
      declinedAt: readDateTime(json, ['declinedAt', 'declined_at']),
      cancelledAt: readDateTime(json, ['cancelledAt', 'cancelled_at']),
      activeAt:
          readDateTime(json, ['activeAt', 'active_at', 'startedAt', 'started_at']),
      pendingClosureAt: readDateTime(
        json,
        ['pendingClosureAt', 'pending_closure_at', 'returnRequestedAt'],
      ),
      closedAt: readDateTime(json, ['closedAt', 'closed_at']),
      specialRequests: readString(
        json,
        ['specialRequests', 'special_requests', 'notes', 'message'],
      ),
      cancellationReason:
          readString(json, ['cancellationReason', 'cancellation_reason']),
      declineReason:
          readString(json, ['declineReason', 'decline_reason', 'rejection_reason']),
      instantBookingEnabled:
          readBool(json, ['instant_booking_enabled', 'instant_booking']) ??
              false,
      agreementStatus: normalizeAgreementStatusValue(
        readString(agreementMap, ['status']) ??
            readString(json, ['agreement_status', 'lease_status']),
      ),
      pricing: BookingPricing.fromJson(json),
    );
  }

  String get displayReference {
    if (bookingNumber.isNotEmpty) return bookingNumber;
    if (id.isNotEmpty) return 'Application $id';
    return 'Application';
  }

  String? get primaryReason {
    if (declineReason != null && declineReason!.trim().isNotEmpty) {
      return declineReason!.trim();
    }
    if (cancellationReason != null && cancellationReason!.trim().isNotEmpty) {
      return cancellationReason!.trim();
    }
    return null;
  }

  bool get hasAgreement =>
      agreementStatus != null && agreementStatus!.trim().isNotEmpty;

  @override
  List<Object?> get props => [
        id,
        bookingNumber,
        status,
        property,
        tenant,
        landlord,
        rentalStartAt,
        rentalEndAt,
        actualReturnAt,
        holdExpiresAt,
        createdAt,
        updatedAt,
        confirmedAt,
        declinedAt,
        cancelledAt,
        activeAt,
        pendingClosureAt,
        closedAt,
        specialRequests,
        cancellationReason,
        declineReason,
        instantBookingEnabled,
        agreementStatus,
        pricing,
      ];
}

String _titleFromEventType(String value) {
  final normalized = _normalizeToken(value);
  switch (normalized) {
    case 'CREATED':
    case 'SUBMITTED':
      return 'Application submitted';
    case 'CONFIRMED':
    case 'APPROVED':
      return 'Application confirmed';
    case 'DECLINED':
      return 'Application declined';
    case 'CANCELLED':
      return 'Application cancelled';
    case 'AGREEMENT_SENT':
      return 'Lease sent for signature';
    case 'CUSTOMER_SIGNED':
    case 'TENANT_SIGNED':
      return 'Tenant signed the lease';
    case 'OWNER_SIGNED':
    case 'LANDLORD_SIGNED':
      return 'Landlord countersigned the lease';
    case 'ACTIVE':
      return 'Tenancy is active';
    case 'PENDING_CLOSURE':
      return 'Move-out is in progress';
    case 'CLOSED':
      return 'Tenancy closed';
    default:
      return titleFromKey(normalized.toLowerCase());
  }
}

class BookingEvent extends Equatable {
  final String id;
  final String eventType;
  final String title;
  final String? description;
  final String? actorLabel;
  final DateTime? createdAt;
  final String? status;
  final Map<String, dynamic> metadata;

  const BookingEvent({
    required this.id,
    required this.eventType,
    required this.title,
    this.description,
    this.actorLabel,
    this.createdAt,
    this.status,
    this.metadata = const <String, dynamic>{},
  });

  factory BookingEvent.fromJson(Map<String, dynamic> json) {
    final metadata = readMap(json, ['metadata', 'metadata_json', 'context']);
    final actorMap = readMap(json, ['actor', 'user']);
    final eventType =
        readString(json, ['eventType', 'event_type', 'type']) ?? 'updated';
    final message = readString(json, ['message', 'title']);

    return BookingEvent(
      id: readString(json, ['id', 'event_id']) ?? '',
      eventType: eventType,
      title: message?.trim().isNotEmpty == true
          ? message!.trim()
          : _titleFromEventType(eventType),
      description:
          readString(json, ['detail', 'description', 'note']) ??
              readString(metadata, ['reason', 'summary']),
      actorLabel: readString(actorMap, ['display_name', 'name', 'username']) ??
          readString(json, ['actor_name']),
      createdAt: readDateTime(
        json,
        ['createdAt', 'created_at', 'occurredAt', 'occurred_at', 'timestamp'],
      ),
      status: normalizeAgreementStatusValue(
            readString(metadata, ['agreement_status', 'lease_status']),
          ) ??
          (readString(metadata, ['status']) != null
              ? normalizeBookingStatus(readString(metadata, ['status'])!)
              : null),
      metadata: metadata,
    );
  }

  @override
  List<Object?> get props => [
        id,
        eventType,
        title,
        description,
        actorLabel,
        createdAt,
        status,
        metadata,
      ];
}
