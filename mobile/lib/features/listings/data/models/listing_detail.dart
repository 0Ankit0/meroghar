import 'package:equatable/equatable.dart';
import 'listing_parsing.dart';
import 'listing_search.dart';

class ListingPhoto extends Equatable {
  final String id;
  final String url;
  final String? thumbnailUrl;
  final String? caption;
  final bool isCover;
  final int position;

  const ListingPhoto({
    this.id = '',
    required this.url,
    this.thumbnailUrl,
    this.caption,
    this.isCover = false,
    this.position = 0,
  });

  factory ListingPhoto.fromJson(Map<String, dynamic> json) {
    final imageUrl =
        readString(json, ['url', 'image_url', 'src', 'thumbnail_url']) ?? '';
    return ListingPhoto(
      id: readString(json, ['id', 'photo_id']) ?? '',
      url: imageUrl,
      thumbnailUrl:
          readString(json, ['thumbnail_url', 'thumb_url']) ?? imageUrl,
      caption: readString(json, ['caption', 'title']),
      isCover: readBool(json, ['is_cover', 'cover']) ?? false,
      position: readInt(json, ['position', 'sort_order']) ?? 0,
    );
  }

  @override
  List<Object?> get props =>
      [id, url, thumbnailUrl, caption, isCover, position];
}

class ListingCategoryRef extends Equatable {
  final String id;
  final String name;
  final String slug;

  const ListingCategoryRef({
    required this.id,
    required this.name,
    required this.slug,
  });

  factory ListingCategoryRef.fromJson(Map<String, dynamic> json) {
    return ListingCategoryRef(
      id: readString(json, ['id', 'category_id', 'property_type_id']) ?? '',
      name: readString(json, ['name', 'label']) ?? 'Category',
      slug: readString(json, ['slug']) ??
          titleFromKey(readString(json, ['name']) ?? 'category')
              .toLowerCase()
              .replaceAll(' ', '-'),
    );
  }

  @override
  List<Object?> get props => [id, name, slug];
}

class ListingPricingOverview extends Equatable {
  final String currency;
  final double? dailyRate;
  final double? weeklyRate;
  final double? monthlyRate;
  final double? depositAmount;
  final String? summary;

  const ListingPricingOverview({
    required this.currency,
    this.dailyRate,
    this.weeklyRate,
    this.monthlyRate,
    this.depositAmount,
    this.summary,
  });

  factory ListingPricingOverview.fromJson(Map<String, dynamic> json) {
    final pricing = readMap(json, ['pricing', 'pricing_overview']);
    final rawRules = readList(json, ['pricing_rules', 'rates']);

    var dailyRate =
        readDouble(pricing, ['daily_rate']) ?? readDouble(json, ['daily_rate']);
    var weeklyRate = readDouble(pricing, ['weekly_rate']) ??
        readDouble(json, ['weekly_rate']);
    var monthlyRate = readDouble(pricing, ['monthly_rate']) ??
        readDouble(json, ['monthly_rate']);
    var currency = readString(pricing, ['currency']) ??
        readString(json, ['currency']) ??
        'NPR';

    for (final rawRule in rawRules) {
      final rule = asJsonMap(rawRule);
      if (rule.isEmpty) continue;
      final rateType = readString(rule, ['rate_type', 'type'])?.toLowerCase();
      final rateAmount = readDouble(rule, ['rate_amount', 'amount', 'value']);
      if (rateAmount == null) continue;
      currency = readString(rule, ['currency']) ?? currency;
      switch (rateType) {
        case 'daily':
          dailyRate ??= rateAmount;
          break;
        case 'weekly':
          weeklyRate ??= rateAmount;
          break;
        case 'monthly':
          monthlyRate ??= rateAmount;
          break;
        default:
          break;
      }
    }

    return ListingPricingOverview(
      currency: currency,
      dailyRate: dailyRate,
      weeklyRate: weeklyRate,
      monthlyRate: monthlyRate,
      depositAmount: readDouble(
            pricing,
            ['deposit_amount', 'security_deposit', 'deposit'],
          ) ??
          readDouble(json, ['deposit_amount', 'security_deposit', 'deposit']),
      summary: readString(pricing, ['summary', 'label']) ??
          readString(json, ['pricing_summary']),
    );
  }

  @override
  List<Object?> get props => [
        currency,
        dailyRate,
        weeklyRate,
        monthlyRate,
        depositAmount,
        summary,
      ];
}

class ListingDetail extends Equatable {
  final String id;
  final String title;
  final String description;
  final String locationAddress;
  final String status;
  final bool isPublished;
  final bool instantBookingEnabled;
  final ListingCategoryRef? category;
  final List<ListingPhoto> photos;
  final List<ListingFact> attributes;
  final List<String> amenities;
  final ListingPricePreview pricePreview;
  final ListingPricingOverview pricingOverview;
  final double? depositAmount;
  final double? averageRating;
  final int reviewCount;
  final String? floorPlanUrl;

  const ListingDetail({
    required this.id,
    required this.title,
    required this.description,
    required this.locationAddress,
    required this.status,
    required this.isPublished,
    required this.instantBookingEnabled,
    required this.photos,
    required this.attributes,
    required this.amenities,
    required this.pricePreview,
    required this.pricingOverview,
    this.category,
    this.depositAmount,
    this.averageRating,
    this.reviewCount = 0,
    this.floorPlanUrl,
  });

  factory ListingDetail.fromJson(Map<String, dynamic> json) {
    final categoryMap = readMap(json, ['category', 'property_type', 'type']);
    final rawPhotos = readList(json, ['photos', 'images', 'media', 'gallery']);
    final photos = rawPhotos
        .map((rawPhoto) {
          if (rawPhoto is String && rawPhoto.trim().isNotEmpty) {
            return ListingPhoto(url: rawPhoto.trim());
          }
          final photo = ListingPhoto.fromJson(asJsonMap(rawPhoto));
          return photo.url.isNotEmpty ? photo : null;
        })
        .whereType<ListingPhoto>()
        .toList()
      ..sort((a, b) => a.position.compareTo(b.position));

    final attributes = listingFactsFromJson(
      readValue(json,
          ['attributes', 'features', 'property_features', 'feature_values']),
    );
    final amenities = listingAmenitiesFromJson(json);
    final pricePreview = ListingPricePreview.fromJson(json);
    final pricingOverview = ListingPricingOverview.fromJson(json);

    return ListingDetail(
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
      category: categoryMap.isNotEmpty
          ? ListingCategoryRef.fromJson(categoryMap)
          : (readString(json, ['category_name', 'property_type_name']) != null
              ? ListingCategoryRef(
                  id: readString(json, ['category_id', 'property_type_id']) ??
                      '',
                  name: readString(
                        json,
                        ['category_name', 'property_type_name'],
                      ) ??
                      'Category',
                  slug: readString(
                        json,
                        ['category_slug', 'property_type_slug'],
                      ) ??
                      '',
                )
              : null),
      photos: photos,
      attributes: attributes,
      amenities: amenities,
      pricePreview: pricePreview,
      pricingOverview: pricingOverview,
      depositAmount: readDouble(
            json,
            ['deposit_amount', 'security_deposit', 'deposit'],
          ) ??
          pricingOverview.depositAmount ??
          pricePreview.depositAmount,
      averageRating: readDouble(json, ['average_rating', 'rating']),
      reviewCount: readInt(json, ['review_count']) ?? 0,
      floorPlanUrl: readString(json, ['floor_plan_url', 'floorplan_url']),
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
        category,
        photos,
        attributes,
        amenities,
        pricePreview,
        pricingOverview,
        depositAmount,
        averageRating,
        reviewCount,
        floorPlanUrl,
      ];
}
