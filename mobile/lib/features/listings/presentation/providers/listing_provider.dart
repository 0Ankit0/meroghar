import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../listing_access.dart';
import '../../data/models/listing_availability.dart';
import '../../data/models/listing_category.dart';
import '../../data/models/listing_detail.dart';
import '../../data/models/listing_search.dart';
import '../../data/models/pricing_quote.dart';
import '../../data/repositories/listing_repository.dart';

final listingsRepositoryProvider = Provider<ListingsRepository>((ref) {
  return ListingsRepository(ref.watch(dioClientProvider));
});

final listingCategoriesProvider = FutureProvider<List<ListingCategory>>((ref) {
  return ref.watch(listingsRepositoryProvider).getCategories();
});

final listingCategoryDetailProvider =
    FutureProvider.family<ListingCategory, String>((ref, categoryId) {
  return ref.watch(listingsRepositoryProvider).getCategoryDetail(categoryId);
});

final listingSearchFiltersProvider = StateProvider<ListingSearchFilters>((ref) {
  return const ListingSearchFilters();
});

final listingSearchResultsProvider =
    FutureProvider<ListingSearchResponse>((ref) {
  final filters = ref.watch(listingSearchFiltersProvider);
  return ref.watch(listingsRepositoryProvider).searchListings(filters);
});

final listingDetailProvider =
    FutureProvider.family<ListingDetail, String>((ref, id) {
  return ref.watch(listingsRepositoryProvider).getListingDetail(id);
});

final listingSelectedPeriodProvider =
    StateProvider.family<ListingDateRange, String>((ref, listingId) {
  return const ListingDateRange();
});

final listingAvailabilityProvider = FutureProvider.family<ListingAvailability?,
    ({String listingId, ListingDateRange period})>((ref, params) async {
  if (!params.period.isComplete) return null;
  return ref
      .watch(listingsRepositoryProvider)
      .getAvailability(params.listingId, params.period);
});

final listingPricingQuoteProvider = FutureProvider.family<PricingQuote?,
    ({String listingId, ListingDateRange period})>((ref, params) async {
  if (!params.period.isComplete) return null;
  return ref
      .watch(listingsRepositoryProvider)
      .getPricingQuote(params.listingId, params.period);
});

final canManageListingsProvider = Provider<bool>((ref) {
  final roles = ref.watch(authNotifierProvider).valueOrNull?.user?.roles ??
      const <String>[];
  return canManageListings(roles);
});
