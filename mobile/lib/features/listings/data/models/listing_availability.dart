import 'package:equatable/equatable.dart';
import 'listing_parsing.dart';
import 'listing_search.dart';

class AvailabilityBlock extends Equatable {
  final String id;
  final String type;
  final String reason;
  final DateTime? startAt;
  final DateTime? endAt;

  const AvailabilityBlock({
    required this.id,
    required this.type,
    required this.reason,
    this.startAt,
    this.endAt,
  });

  factory AvailabilityBlock.fromJson(Map<String, dynamic> json) {
    return AvailabilityBlock(
      id: readString(json, ['id', 'block_id']) ?? '',
      type: readString(json, ['block_type', 'type']) ?? 'blocked',
      reason: readString(json, ['reason', 'note', 'label']) ?? '',
      startAt: readDateTime(json, ['start_at', 'start', 'from']),
      endAt: readDateTime(json, ['end_at', 'end', 'to']),
    );
  }

  @override
  List<Object?> get props => [id, type, reason, startAt, endAt];
}

class ListingAvailability extends Equatable {
  final String propertyId;
  final ListingDateRange period;
  final bool isAvailable;
  final List<AvailabilityBlock> blockedPeriods;
  final DateTime? nextAvailableStart;
  final DateTime? nextAvailableEnd;
  final String? note;

  const ListingAvailability({
    required this.propertyId,
    required this.period,
    required this.isAvailable,
    this.blockedPeriods = const [],
    this.nextAvailableStart,
    this.nextAvailableEnd,
    this.note,
  });

  factory ListingAvailability.fromJson(
    Map<String, dynamic> json, {
    required ListingDateRange requestedPeriod,
  }) {
    final availability = readMap(json, ['availability']);
    final source = availability.isNotEmpty ? availability : json;
    final blocks = readList(
      source,
      [
        'blocks',
        'blocked_periods',
        'availability_blocks',
        'unavailable_periods'
      ],
    )
        .map((rawBlock) => AvailabilityBlock.fromJson(asJsonMap(rawBlock)))
        .toList();

    return ListingAvailability(
      propertyId: readString(source, ['property_id', 'id']) ??
          readString(json, ['property_id', 'id']) ??
          '',
      period: requestedPeriod,
      isAvailable:
          readBool(source, ['available', 'is_available', 'isAvailable']) ??
              blocks.isEmpty,
      blockedPeriods: blocks,
      nextAvailableStart: readDateTime(
        source,
        ['next_available_start', 'next_available_at', 'available_from'],
      ),
      nextAvailableEnd: readDateTime(
        source,
        ['next_available_end', 'available_until'],
      ),
      note: readString(source, ['message', 'note', 'reason']),
    );
  }

  @override
  List<Object?> get props => [
        propertyId,
        period,
        isAvailable,
        blockedPeriods,
        nextAvailableStart,
        nextAvailableEnd,
        note,
      ];
}
