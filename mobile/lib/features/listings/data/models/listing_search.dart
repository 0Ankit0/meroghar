import 'package:equatable/equatable.dart';
import 'package:intl/intl.dart';
import 'listing_parsing.dart';

DateTime _startOfDay(DateTime value) =>
    DateTime(value.year, value.month, value.day);

DateTime _endOfDay(DateTime value) =>
    DateTime(value.year, value.month, value.day, 23, 59, 59);

class ListingDateRange extends Equatable {
  final DateTime? start;
  final DateTime? end;

  const ListingDateRange({this.start, this.end});

  bool get isComplete => start != null && end != null;
  bool get isEmpty => start == null && end == null;

  String get label {
    if (!isComplete) return 'Any time';
    final formatter = DateFormat('MMM d, y');
    return '${formatter.format(start!)} – ${formatter.format(end!)}';
  }

  int get totalDays {
    if (!isComplete) return 0;
    return _endOfDay(end!).difference(_startOfDay(start!)).inDays + 1;
  }

  String? get startQueryValue =>
      start == null ? null : _startOfDay(start!).toIso8601String();

  String? get endQueryValue =>
      end == null ? null : _endOfDay(end!).toIso8601String();

  ListingDateRange copyWith({
    DateTime? start,
    DateTime? end,
    bool clear = false,
  }) {
    if (clear) return const ListingDateRange();
    return ListingDateRange(
      start: start ?? this.start,
      end: end ?? this.end,
    );
  }

  @override
  List<Object?> get props => [start, end];
}

class ListingSearchFilters extends Equatable {
  final String? categoryId;
  final String? categorySlug;
  final String location;
  final double? minPrice;
  final double? maxPrice;
  final double? radiusKm;
  final ListingDateRange period;
  final int page;
  final int perPage;

  const ListingSearchFilters({
    this.categoryId,
    this.categorySlug,
    this.location = '',
    this.minPrice,
    this.maxPrice,
    this.radiusKm,
    this.period = const ListingDateRange(),
    this.page = 1,
    this.perPage = 10,
  });

  bool get hasActiveFilters {
    return (categorySlug?.isNotEmpty ?? false) ||
        location.trim().isNotEmpty ||
        minPrice != null ||
        maxPrice != null ||
        radiusKm != null ||
        period.isComplete;
  }

  Map<String, dynamic> toQueryParameters() {
    final params = <String, dynamic>{
      'page': page,
      'per_page': perPage,
    };

    if (categorySlug != null && categorySlug!.isNotEmpty) {
      params['category'] = categorySlug;
    }
    if (location.trim().isNotEmpty) {
      params['location'] = location.trim();
    }
    if (radiusKm != null) {
      params['radius_km'] = radiusKm;
    }
    if (minPrice != null) {
      params['min_price'] = minPrice;
    }
    if (maxPrice != null) {
      params['max_price'] = maxPrice;
    }
    if (period.startQueryValue != null) {
      params['start'] = period.startQueryValue;
    }
    if (period.endQueryValue != null) {
      params['end'] = period.endQueryValue;
    }

    return params;
  }

  ListingSearchFilters copyWith({
    String? categoryId,
    String? categorySlug,
    String? location,
    double? minPrice,
    double? maxPrice,
    double? radiusKm,
    ListingDateRange? period,
    int? page,
    int? perPage,
    bool clearCategory = false,
    bool clearPriceRange = false,
    bool clearRadius = false,
    bool clearPeriod = false,
  }) {
    return ListingSearchFilters(
      categoryId: clearCategory ? null : (categoryId ?? this.categoryId),
      categorySlug: clearCategory ? null : (categorySlug ?? this.categorySlug),
      location: location ?? this.location,
      minPrice: clearPriceRange ? null : (minPrice ?? this.minPrice),
      maxPrice: clearPriceRange ? null : (maxPrice ?? this.maxPrice),
      radiusKm: clearRadius ? null : (radiusKm ?? this.radiusKm),
      period: clearPeriod ? const ListingDateRange() : (period ?? this.period),
      page: page ?? this.page,
      perPage: perPage ?? this.perPage,
    );
  }

  @override
  List<Object?> get props => [
        categoryId,
        categorySlug,
        location,
        minPrice,
        maxPrice,
        radiusKm,
        period,
        page,
        perPage,
      ];
}

class ListingFact extends Equatable {
  final String label;
  final String value;
  final String? slug;

  const ListingFact({
    required this.label,
    required this.value,
    this.slug,
  });

  @override
  List<Object?> get props => [label, value, slug];
}

List<ListingFact> _deduplicateFacts(List<ListingFact> facts) {
  final seen = <String>{};
  return facts.where((fact) {
    final key = (fact.slug ?? fact.label).toLowerCase();
    if (!seen.add(key)) return false;
    return fact.value.trim().isNotEmpty;
  }).toList();
}

List<ListingFact> listingFactsFromJson(dynamic raw) {
  if (raw is List) {
    return _deduplicateFacts(raw
        .map((item) => asJsonMap(item))
        .where((item) => item.isNotEmpty)
        .map((item) => ListingFact(
              label: readString(item, ['label', 'name', 'slug', 'key']) ??
                  'Detail',
              value: readString(item, ['value', 'display_value', 'text']) ?? '',
              slug: readString(item, ['slug', 'key']),
            ))
        .where((fact) => fact.value.isNotEmpty)
        .toList());
  }

  final rawMap = asJsonMap(raw);
  if (rawMap.isEmpty) return const [];

  final facts = <ListingFact>[];
  for (final entry in rawMap.entries) {
    final value = entry.value;
    if (value == null || value is Map || value is List) continue;
    final displayValue = value.toString().trim();
    if (displayValue.isEmpty) continue;
    facts.add(ListingFact(
      label: titleFromKey(entry.key),
      value: displayValue,
      slug: entry.key,
    ));
  }

  return _deduplicateFacts(facts);
}

List<String> listingAmenitiesFromJson(Map<String, dynamic> json) {
  final amenities = readStringList(
    json,
    ['amenities', 'amenity_names', 'amenity_list'],
  );
  return amenities.toSet().toList();
}

String _inferCadence(Map<String, dynamic> json) {
  if (json.containsKey('monthly_rate')) return 'month';
  if (json.containsKey('weekly_rate')) return 'week';
  if (json.containsKey('daily_rate')) return 'day';
  return '';
}

String _formatMoney(double amount) {
  if (amount % 1 == 0) return amount.toStringAsFixed(0);
  return amount.toStringAsFixed(2);
}

String? _extractImageUrl(dynamic rawPhoto) {
  if (rawPhoto is String && rawPhoto.trim().isNotEmpty) {
    return rawPhoto.trim();
  }
  final photo = asJsonMap(rawPhoto);
  if (photo.isEmpty) return null;
  return readString(photo, ['thumbnail_url', 'url', 'image_url', 'src']);
}

String? _extractCoverImage(List<dynamic> rawPhotos) {
  for (final rawPhoto in rawPhotos) {
    final photo = asJsonMap(rawPhoto);
    if (photo.isEmpty) continue;
    if (readBool(photo, ['is_cover', 'cover']) == true) {
      return _extractImageUrl(photo);
    }
  }
  if (rawPhotos.isEmpty) return null;
  return _extractImageUrl(rawPhotos.first);
}

int? _factToInt(List<ListingFact> facts, List<String> slugs) {
  for (final fact in facts) {
    final slug = fact.slug?.toLowerCase() ?? '';
    if (!slugs.any(slug.contains)) continue;
    return int.tryParse(fact.value);
  }
  return null;
}

class ListingPricePreview extends Equatable {
  final String currency;
  final double? amount;
  final String cadence;
  final String? label;
  final double? depositAmount;

  const ListingPricePreview({
    required this.currency,
    this.amount,
    this.cadence = '',
    this.label,
    this.depositAmount,
  });

  factory ListingPricePreview.fromJson(Map<String, dynamic> json) {
    final nested = readMap(json, ['pricing_preview', 'pricing', 'price']);
    final source = nested.isNotEmpty ? nested : json;
    final amount = readDouble(source, [
      'amount',
      'value',
      'starting_price',
      'min_price',
      'price',
      'monthly_rate',
      'weekly_rate',
      'daily_rate',
      'base_rate',
      'rent',
    ]);

    return ListingPricePreview(
      currency: readString(source, ['currency']) ??
          readString(json, ['currency']) ??
          'NPR',
      amount: amount,
      cadence: readString(
              source, ['cadence', 'unit', 'rate_type', 'pricing_unit']) ??
          _inferCadence(source),
      label: readString(source, ['label', 'display', 'summary']),
      depositAmount:
          readDouble(source, ['deposit_amount', 'security_deposit', 'deposit']),
    );
  }

  String get displayLabel {
    if (amount == null) return 'Pricing on request';
    final amountText = '${currency.toUpperCase()} ${_formatMoney(amount!)}';
    if (label != null && label!.trim().isNotEmpty) {
      return '$amountText · ${label!.trim()}';
    }
    if (cadence.isNotEmpty) {
      return '$amountText / $cadence';
    }
    return amountText;
  }

  @override
  List<Object?> get props => [currency, amount, cadence, label, depositAmount];
}

class ListingSummary extends Equatable {
  final String id;
  final String title;
  final String description;
  final String locationAddress;
  final String status;
  final bool isPublished;
  final bool instantBookingEnabled;
  final String? categoryId;
  final String? categoryName;
  final String? categorySlug;
  final String? coverImageUrl;
  final List<String> imageUrls;
  final ListingPricePreview pricePreview;
  final double? depositAmount;
  final double? averageRating;
  final int reviewCount;
  final int? bedrooms;
  final int? bathrooms;
  final List<ListingFact> facts;
  final List<String> amenities;

  const ListingSummary({
    required this.id,
    required this.title,
    required this.description,
    required this.locationAddress,
    required this.status,
    required this.isPublished,
    required this.instantBookingEnabled,
    required this.pricePreview,
    this.categoryId,
    this.categoryName,
    this.categorySlug,
    this.coverImageUrl,
    this.imageUrls = const [],
    this.depositAmount,
    this.averageRating,
    this.reviewCount = 0,
    this.bedrooms,
    this.bathrooms,
    this.facts = const [],
    this.amenities = const [],
  });

  factory ListingSummary.fromJson(Map<String, dynamic> json) {
    final category = readMap(json, ['category', 'property_type', 'type']);
    final rawPhotos = readList(json, ['photos', 'images', 'media', 'gallery']);
    final imageUrls = rawPhotos
        .map(_extractImageUrl)
        .whereType<String>()
        .where((url) => url.isNotEmpty)
        .toList();
    final facts = listingFactsFromJson(
      readValue(json,
          ['attributes', 'features', 'property_features', 'feature_values']),
    );
    final pricePreview = ListingPricePreview.fromJson(json);

    return ListingSummary(
      id: readString(json, ['id', 'property_id', 'asset_id']) ?? '',
      title: readString(json, ['title', 'name']) ?? 'Untitled listing',
      description: readString(json, ['description', 'summary']) ?? '',
      locationAddress: readString(
            json,
            ['location_address', 'address', 'location', 'city'],
          ) ??
          'Location unavailable',
      status: readString(json, ['status']) ??
          ((readBool(json, ['is_published', 'published']) ?? false)
              ? 'published'
              : 'draft'),
      isPublished: readBool(json, ['is_published', 'published']) ??
          (readString(json, ['status'])?.toLowerCase() == 'published'),
      instantBookingEnabled:
          readBool(json, ['instant_booking_enabled', 'instant_booking']) ??
              false,
      categoryId: readString(
            category,
            ['id', 'category_id', 'property_type_id'],
          ) ??
          readString(json, ['category_id', 'property_type_id']),
      categoryName: readString(category, ['name', 'label']) ??
          readString(json, ['category_name', 'property_type_name']),
      categorySlug: readString(category, ['slug']) ??
          readString(json, ['category_slug', 'property_type_slug']),
      coverImageUrl: _extractCoverImage(rawPhotos) ??
          readString(json, ['cover_image_url', 'image_url', 'thumbnail_url']),
      imageUrls: imageUrls,
      pricePreview: pricePreview,
      depositAmount: readDouble(
            json,
            ['deposit_amount', 'security_deposit', 'deposit'],
          ) ??
          pricePreview.depositAmount,
      averageRating: readDouble(json, ['average_rating', 'rating']),
      reviewCount: readInt(json, ['review_count']) ?? 0,
      bedrooms: readInt(json, ['bedrooms', 'bedroom_count']) ??
          _factToInt(facts, ['bedroom']),
      bathrooms: readInt(json, ['bathrooms', 'bathroom_count']) ??
          _factToInt(facts, ['bathroom']),
      facts: facts,
      amenities: listingAmenitiesFromJson(json),
    );
  }

  @override
  List<Object?> get props => [
        id,
        title,
        description,
        locationAddress,
        status,
        isPublished,
        instantBookingEnabled,
        categoryId,
        categoryName,
        categorySlug,
        coverImageUrl,
        imageUrls,
        pricePreview,
        depositAmount,
        averageRating,
        reviewCount,
        bedrooms,
        bathrooms,
        facts,
        amenities,
      ];
}

class ListingSearchResponse extends Equatable {
  final List<ListingSummary> items;
  final int page;
  final int perPage;
  final int total;
  final bool hasMore;

  const ListingSearchResponse({
    required this.items,
    this.page = 1,
    this.perPage = 10,
    this.total = 0,
    this.hasMore = false,
  });

  bool get isEmpty => items.isEmpty;

  factory ListingSearchResponse.fromJson(Map<String, dynamic> json) {
    final meta = readMap(json, ['meta']);
    final rawItems =
        readList(json, ['items', 'results', 'assets', 'properties']);
    final items = rawItems
        .map((item) => ListingSummary.fromJson(asJsonMap(item)))
        .where((item) => item.id.isNotEmpty || item.title.isNotEmpty)
        .toList();
    final page =
        readInt(meta, ['page', 'current_page']) ?? readInt(json, ['page']) ?? 1;
    final perPage = readInt(meta, ['perPage', 'per_page']) ??
        readInt(json, ['per_page', 'limit']) ??
        (items.isEmpty ? 10 : items.length);
    final total = readInt(meta, ['total', 'count']) ??
        readInt(json, ['total', 'count']) ??
        items.length;

    return ListingSearchResponse(
      items: items,
      page: page,
      perPage: perPage,
      total: total,
      hasMore: readBool(meta, ['hasMore', 'has_more']) ??
          readBool(json, ['has_more']) ??
          (page * perPage < total),
    );
  }

  @override
  List<Object?> get props => [items, page, perPage, total, hasMore];
}
