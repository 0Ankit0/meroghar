import '../../../../core/error/app_exception.dart';
import '../../../../core/error/error_handler.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/network/dio_client.dart';
import '../models/create_listing_request.dart';
import '../models/listing_availability.dart';
import '../models/listing_category.dart';
import '../models/listing_detail.dart';
import '../models/listing_parsing.dart';
import '../models/listing_search.dart';
import '../models/pricing_quote.dart';

class ListingsRepository {
  final DioClient _dioClient;

  ListingsRepository(this._dioClient);

  Future<List<ListingCategory>> getCategories() async {
    try {
      final response = await _dioClient.dio.get(ApiEndpoints.categories);
      final rawCategories = _extractList(
        response.data,
        collectionKeys: const ['categories', 'items', 'results'],
      );
      final categories = rawCategories
          .map((item) => ListingCategory.fromJson(asJsonMap(item)))
          .where(
              (category) => category.id.isNotEmpty || category.slug.isNotEmpty)
          .toList()
        ..sort((a, b) {
          final byOrder = a.displayOrder.compareTo(b.displayOrder);
          if (byOrder != 0) return byOrder;
          return a.name.compareTo(b.name);
        });
      return categories;
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<ListingCategory> getCategoryDetail(String categoryId) async {
    try {
      final response =
          await _dioClient.dio.get(ApiEndpoints.categoryById(categoryId));
      return ListingCategory.fromJson(_extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<ListingSearchResponse> searchListings(
      ListingSearchFilters filters) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.assets,
        queryParameters: filters.toQueryParameters(),
      );
      return ListingSearchResponse.fromJson(
          _normalizeSearchPayload(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<ListingDetail> getListingDetail(String propertyId) async {
    try {
      final response =
          await _dioClient.dio.get(ApiEndpoints.propertyById(propertyId));
      return ListingDetail.fromJson(_extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<ListingAvailability> getAvailability(
    String propertyId,
    ListingDateRange period,
  ) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.propertyAvailability(propertyId),
        queryParameters: {
          'start': period.startQueryValue,
          'end': period.endQueryValue,
        },
      );
      return ListingAvailability.fromJson(
        _extractRequiredMap(response.data),
        requestedPeriod: period,
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<PricingQuote> getPricingQuote(
    String propertyId,
    ListingDateRange period,
  ) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.propertyPrice(propertyId),
        queryParameters: {
          'start': period.startQueryValue,
          'end': period.endQueryValue,
        },
      );
      return PricingQuote.fromJson(
        _extractRequiredMap(response.data),
        requestedPeriod: period,
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<ListingDetail> createListingDraft(CreateListingRequest request) async {
    try {
      final response = await _dioClient.dio.post(
        ApiEndpoints.assets,
        data: request.toJson(),
      );
      return ListingDetail.fromJson(_extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  dynamic _extractData(dynamic payload) {
    final map = asJsonMap(payload);
    if (map.containsKey('data')) return map['data'];
    return payload;
  }

  List<dynamic> _extractList(
    dynamic payload, {
    Iterable<String> collectionKeys = const [],
  }) {
    final extracted = _extractData(payload);
    final extractedList = asJsonList(extracted);
    if (extractedList.isNotEmpty) return extractedList;

    final extractedMap = asJsonMap(extracted);
    for (final key in collectionKeys) {
      final collection = asJsonList(extractedMap[key]);
      if (collection.isNotEmpty) return collection;
    }

    final root = asJsonMap(payload);
    for (final key in collectionKeys) {
      final collection = asJsonList(root[key]);
      if (collection.isNotEmpty) return collection;
    }

    return const <dynamic>[];
  }

  Map<String, dynamic> _extractMap(dynamic payload) {
    final extracted = _extractData(payload);
    final extractedMap = asJsonMap(extracted);
    if (extractedMap.isNotEmpty) return extractedMap;
    return asJsonMap(payload);
  }

  Map<String, dynamic> _extractRequiredMap(dynamic payload) {
    final map = _extractMap(payload);
    if (map.isEmpty) {
      throw const ServerException(message: 'Unexpected response format.');
    }
    return map;
  }

  Map<String, dynamic> _normalizeSearchPayload(dynamic payload) {
    final root = asJsonMap(payload);
    final meta = asJsonMap(root['meta']);
    final extracted = _extractData(payload);
    final extractedList = asJsonList(extracted);

    if (extractedList.isNotEmpty) {
      return {
        'items': extractedList,
        if (meta.isNotEmpty) 'meta': meta,
      };
    }

    final extractedMap = asJsonMap(extracted);
    if (extractedMap.isNotEmpty) {
      return {
        ...extractedMap,
        if (meta.isNotEmpty && !extractedMap.containsKey('meta')) 'meta': meta,
      };
    }

    return root.isNotEmpty
        ? root
        : const <String, dynamic>{'items': <dynamic>[]};
  }
}
