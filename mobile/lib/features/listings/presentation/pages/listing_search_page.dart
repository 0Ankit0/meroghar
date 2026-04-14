import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/error/error_handler.dart';
import '../../data/models/listing_category.dart';
import '../../data/models/listing_search.dart';
import '../providers/listing_provider.dart';

class ListingSearchPage extends ConsumerStatefulWidget {
  const ListingSearchPage({super.key});

  @override
  ConsumerState<ListingSearchPage> createState() => _ListingSearchPageState();
}

class _ListingSearchPageState extends ConsumerState<ListingSearchPage> {
  late final TextEditingController _locationController;
  late final TextEditingController _minPriceController;
  late final TextEditingController _maxPriceController;
  late final TextEditingController _radiusController;
  String? _selectedCategoryId;
  ListingDateRange _selectedPeriod = const ListingDateRange();

  @override
  void initState() {
    super.initState();
    final filters = ref.read(listingSearchFiltersProvider);
    _locationController = TextEditingController(text: filters.location);
    _minPriceController = TextEditingController(
      text: filters.minPrice?.toStringAsFixed(0) ?? '',
    );
    _maxPriceController = TextEditingController(
      text: filters.maxPrice?.toStringAsFixed(0) ?? '',
    );
    _radiusController = TextEditingController(
      text: filters.radiusKm?.toStringAsFixed(0) ?? '',
    );
    _selectedCategoryId = filters.categoryId;
    _selectedPeriod = filters.period;
  }

  @override
  void dispose() {
    _locationController.dispose();
    _minPriceController.dispose();
    _maxPriceController.dispose();
    _radiusController.dispose();
    super.dispose();
  }

  double? _parseDouble(String value) {
    final trimmed = value.trim();
    if (trimmed.isEmpty) return null;
    return double.tryParse(trimmed);
  }

  ListingCategory? _findCategoryById(
      List<ListingCategory> categories, String? id) {
    if (id == null || id.isEmpty) return null;
    for (final category in categories) {
      if (category.id == id) return category;
    }
    return null;
  }

  Future<void> _pickDateRange() async {
    final now = DateTime.now();
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(now.year, now.month, now.day),
      lastDate: DateTime(now.year + 2, now.month, now.day),
      initialDateRange: _selectedPeriod.isComplete
          ? DateTimeRange(
              start: _selectedPeriod.start!,
              end: _selectedPeriod.end!,
            )
          : null,
    );

    if (picked == null) return;

    setState(() {
      _selectedPeriod = ListingDateRange(
        start: picked.start,
        end: picked.end,
      );
    });
  }

  void _applyFilters() {
    final categories =
        ref.read(listingCategoriesProvider).valueOrNull ?? const [];
    final category = _findCategoryById(categories, _selectedCategoryId);

    ref.read(listingSearchFiltersProvider.notifier).state =
        ListingSearchFilters(
      categoryId: category?.id,
      categorySlug: category?.slug,
      location: _locationController.text.trim(),
      minPrice: _parseDouble(_minPriceController.text),
      maxPrice: _parseDouble(_maxPriceController.text),
      radiusKm: _parseDouble(_radiusController.text),
      period: _selectedPeriod,
    );
  }

  void _clearFilters() {
    setState(() {
      _selectedCategoryId = null;
      _selectedPeriod = const ListingDateRange();
      _locationController.clear();
      _minPriceController.clear();
      _maxPriceController.clear();
      _radiusController.clear();
    });
    ref.read(listingSearchFiltersProvider.notifier).state =
        const ListingSearchFilters();
  }

  Future<void> _refresh() async {
    ref.invalidate(listingCategoriesProvider);
    ref.invalidate(listingSearchResultsProvider);
    try {
      await ref.read(listingSearchResultsProvider.future);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final categoriesAsync = ref.watch(listingCategoriesProvider);
    final resultsAsync = ref.watch(listingSearchResultsProvider);
    final currentFilters = ref.watch(listingSearchFiltersProvider);
    final canManage = ref.watch(canManageListingsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Discover listings'),
        actions: [
          if (canManage)
            IconButton(
              tooltip: 'Create draft listing',
              icon: const Icon(Icons.add_home_work_outlined),
              onPressed: () => context.push(AppConstants.manageListingsRoute),
            ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          children: [
            _ListingFilterCard(
              categoriesAsync: categoriesAsync,
              selectedCategoryId: _selectedCategoryId,
              locationController: _locationController,
              minPriceController: _minPriceController,
              maxPriceController: _maxPriceController,
              radiusController: _radiusController,
              selectedPeriod: _selectedPeriod,
              onCategoryChanged: (value) =>
                  setState(() => _selectedCategoryId = value),
              onPickDates: _pickDateRange,
              onApply: _applyFilters,
              onClear: _clearFilters,
            ),
            const SizedBox(height: 16),
            _ResultsHeader(
              totalResults: resultsAsync.valueOrNull?.total ?? 0,
              activeFilters: currentFilters,
            ),
            const SizedBox(height: 12),
            resultsAsync.when(
              loading: () => const Padding(
                padding: EdgeInsets.symmetric(vertical: 48),
                child: Center(child: CircularProgressIndicator.adaptive()),
              ),
              error: (error, _) => _ErrorState(
                message: ErrorHandler.handle(error).message,
                onRetry: () => ref.invalidate(listingSearchResultsProvider),
              ),
              data: (results) {
                if (results.items.isEmpty) {
                  return _EmptyResultsState(
                    hasFilters: currentFilters.hasActiveFilters,
                    onClearFilters: _clearFilters,
                  );
                }

                return Column(
                  children: [
                    for (final listing in results.items) ...[
                      _ListingCard(
                        listing: listing,
                        onTap: () => context
                            .push(AppConstants.listingDetailRoute(listing.id)),
                      ),
                      const SizedBox(height: 12),
                    ],
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _ListingFilterCard extends StatelessWidget {
  final AsyncValue<List<ListingCategory>> categoriesAsync;
  final String? selectedCategoryId;
  final TextEditingController locationController;
  final TextEditingController minPriceController;
  final TextEditingController maxPriceController;
  final TextEditingController radiusController;
  final ListingDateRange selectedPeriod;
  final ValueChanged<String?> onCategoryChanged;
  final Future<void> Function() onPickDates;
  final VoidCallback onApply;
  final VoidCallback onClear;

  const _ListingFilterCard({
    required this.categoriesAsync,
    required this.selectedCategoryId,
    required this.locationController,
    required this.minPriceController,
    required this.maxPriceController,
    required this.radiusController,
    required this.selectedPeriod,
    required this.onCategoryChanged,
    required this.onPickDates,
    required this.onApply,
    required this.onClear,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Search rentals',
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            Text(
              'Filter by property type, stay period, location, and budget.',
              style: theme.textTheme.bodySmall,
            ),
            const SizedBox(height: 16),
            categoriesAsync.when(
              data: (categories) => DropdownButtonFormField<String?>(
                key: ValueKey(selectedCategoryId),
                initialValue: selectedCategoryId,
                decoration: const InputDecoration(
                  labelText: 'Property type',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.apartment_outlined),
                ),
                items: [
                  const DropdownMenuItem<String?>(
                    value: null,
                    child: Text('All categories'),
                  ),
                  ...categories.map(
                    (category) => DropdownMenuItem<String?>(
                      value: category.id,
                      child: Text(category.name),
                    ),
                  ),
                ],
                onChanged: onCategoryChanged,
              ),
              loading: () => const LinearProgressIndicator(),
              error: (error, _) => Text(
                'Could not load property categories: ${ErrorHandler.handle(error).message}',
                style: TextStyle(color: theme.colorScheme.error),
              ),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: locationController,
              decoration: const InputDecoration(
                labelText: 'Location',
                hintText: 'Kathmandu, Lalitpur, Bhaktapur...',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.location_on_outlined),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: minPriceController,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                      labelText: 'Min price',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.currency_rupee_outlined),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextFormField(
                    controller: maxPriceController,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                      labelText: 'Max price',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.currency_rupee_outlined),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: radiusController,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Radius (km)',
                hintText: 'Optional',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.radar_outlined),
              ),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: onPickDates,
              icon: const Icon(Icons.calendar_today_outlined),
              label: Align(
                alignment: Alignment.centerLeft,
                child: Text(selectedPeriod.label),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: onApply,
                    icon: const Icon(Icons.search),
                    label: const Text('Search'),
                  ),
                ),
                const SizedBox(width: 12),
                TextButton(
                  onPressed: onClear,
                  child: const Text('Clear'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _ResultsHeader extends StatelessWidget {
  final int totalResults;
  final ListingSearchFilters activeFilters;

  const _ResultsHeader({
    required this.totalResults,
    required this.activeFilters,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Listings',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
              Text(
                totalResults > 0
                    ? '$totalResults result${totalResults == 1 ? '' : 's'}'
                    : 'Browse currently discoverable listings',
                style: theme.textTheme.bodySmall,
              ),
            ],
          ),
        ),
        if (activeFilters.period.isComplete)
          Chip(
            avatar: const Icon(Icons.calendar_today_outlined, size: 16),
            label: Text(activeFilters.period.label),
          ),
      ],
    );
  }
}

class _ListingCard extends StatelessWidget {
  final ListingSummary listing;
  final VoidCallback onTap;

  const _ListingCard({
    required this.listing,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final highlights = <Widget>[
      if (listing.bedrooms != null)
        _FactChip(
          icon: Icons.bed_outlined,
          label: '${listing.bedrooms} bed',
        ),
      if (listing.bathrooms != null)
        _FactChip(
          icon: Icons.bathtub_outlined,
          label: '${listing.bathrooms} bath',
        ),
      if (listing.instantBookingEnabled)
        const _FactChip(
          icon: Icons.flash_on_outlined,
          label: 'Instant booking',
        ),
    ];

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _ListingImage(imageUrl: listing.coverImageUrl),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      if (listing.categoryName != null &&
                          listing.categoryName!.isNotEmpty)
                        Chip(label: Text(listing.categoryName!)),
                      Chip(
                        label: Text(
                          listing.isPublished ? 'Published' : listing.status,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    listing.title,
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      const Icon(Icons.location_on_outlined, size: 18),
                      const SizedBox(width: 4),
                      Expanded(
                        child: Text(
                          listing.locationAddress,
                          style: theme.textTheme.bodyMedium,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    listing.pricePreview.displayLabel,
                    style: theme.textTheme.titleSmall?.copyWith(
                      color: theme.colorScheme.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  if (listing.depositAmount != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      'Deposit: NPR ${listing.depositAmount!.toStringAsFixed(0)}',
                      style: theme.textTheme.bodySmall,
                    ),
                  ],
                  if (highlights.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: highlights,
                    ),
                  ],
                  if (listing.description.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Text(
                      listing.description,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodyMedium,
                    ),
                  ],
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton.icon(
                      onPressed: onTap,
                      icon: const Icon(Icons.chevron_right),
                      label: const Text('View details'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ListingImage extends StatelessWidget {
  final String? imageUrl;

  const _ListingImage({this.imageUrl});

  @override
  Widget build(BuildContext context) {
    if (imageUrl == null || imageUrl!.isEmpty) {
      return Container(
        height: 180,
        width: double.infinity,
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        child: const Icon(Icons.home_work_outlined, size: 48),
      );
    }

    return SizedBox(
      height: 180,
      width: double.infinity,
      child: CachedNetworkImage(
        imageUrl: imageUrl!,
        fit: BoxFit.cover,
        errorWidget: (_, __, ___) => Container(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          child: const Icon(Icons.broken_image_outlined, size: 40),
        ),
        placeholder: (_, __) => Container(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          child: const Center(child: CircularProgressIndicator.adaptive()),
        ),
      ),
    );
  }
}

class _FactChip extends StatelessWidget {
  final IconData icon;
  final String label;

  const _FactChip({
    required this.icon,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(999),
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16),
          const SizedBox(width: 6),
          Text(label),
        ],
      ),
    );
  }
}

class _EmptyResultsState extends StatelessWidget {
  final bool hasFilters;
  final VoidCallback onClearFilters;

  const _EmptyResultsState({
    required this.hasFilters,
    required this.onClearFilters,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const Icon(Icons.travel_explore_outlined, size: 48),
            const SizedBox(height: 12),
            Text(
              hasFilters
                  ? 'No listings match your current filters.'
                  : 'No listings are available right now.',
              textAlign: TextAlign.center,
            ),
            if (hasFilters) ...[
              const SizedBox(height: 12),
              TextButton(
                onPressed: onClearFilters,
                child: const Text('Clear filters'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorState({
    required this.message,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 48),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: onRetry,
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}
