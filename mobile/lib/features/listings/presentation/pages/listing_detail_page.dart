import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/error/error_handler.dart';
import '../../../applications/data/models/create_booking_request.dart';
import '../../../applications/presentation/providers/booking_provider.dart';
import '../../data/models/listing_availability.dart';
import '../../data/models/listing_detail.dart';
import '../../data/models/listing_search.dart';
import '../../data/models/pricing_quote.dart';
import '../../../payments/presentation/providers/payment_provider.dart';
import '../providers/listing_provider.dart';

class ListingDetailPage extends ConsumerStatefulWidget {
  final String listingId;

  const ListingDetailPage({
    super.key,
    required this.listingId,
  });

  @override
  ConsumerState<ListingDetailPage> createState() => _ListingDetailPageState();
}

class _ListingDetailPageState extends ConsumerState<ListingDetailPage> {
  int _photoIndex = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final current = ref.read(listingSelectedPeriodProvider(widget.listingId));
      if (current.isComplete) return;
      final searchPeriod = ref.read(listingSearchFiltersProvider).period;
      if (!searchPeriod.isComplete) return;
      ref.read(listingSelectedPeriodProvider(widget.listingId).notifier).state =
          searchPeriod;
    });
  }

  Future<void> _pickDateRange(ListingDateRange currentPeriod) async {
    final now = DateTime.now();
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(now.year, now.month, now.day),
      lastDate: DateTime(now.year + 2, now.month, now.day),
      initialDateRange: currentPeriod.isComplete
          ? DateTimeRange(
              start: currentPeriod.start!,
              end: currentPeriod.end!,
            )
          : null,
    );

    if (picked == null) return;

    ref.read(listingSelectedPeriodProvider(widget.listingId).notifier).state =
        ListingDateRange(start: picked.start, end: picked.end);
  }

  Future<void> _refresh(ListingDateRange period) async {
    ref.invalidate(listingDetailProvider(widget.listingId));
    if (period.isComplete) {
      final availabilityParams = (
        listingId: widget.listingId,
        period: period,
      );
      ref.invalidate(listingAvailabilityProvider(availabilityParams));
      ref.invalidate(listingPricingQuoteProvider(availabilityParams));
    }
    try {
      await ref.read(listingDetailProvider(widget.listingId).future);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final detailAsync = ref.watch(listingDetailProvider(widget.listingId));
    final selectedPeriod =
        ref.watch(listingSelectedPeriodProvider(widget.listingId));
    final availabilityAsync = ref.watch(listingAvailabilityProvider((
      listingId: widget.listingId,
      period: selectedPeriod,
    )));
    final quoteAsync = ref.watch(listingPricingQuoteProvider((
      listingId: widget.listingId,
      period: selectedPeriod,
    )));

    return Scaffold(
      appBar: AppBar(title: const Text('Listing details')),
      body: detailAsync.when(
        loading: () =>
            const Center(child: CircularProgressIndicator.adaptive()),
        error: (error, _) => _DetailErrorState(
          message: ErrorHandler.handle(error).message,
          onRetry: () =>
              ref.invalidate(listingDetailProvider(widget.listingId)),
        ),
        data: (detail) => RefreshIndicator(
          onRefresh: () => _refresh(selectedPeriod),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              _ListingGallery(
                photos: detail.photos,
                currentIndex: _photoIndex,
                onPageChanged: (index) => setState(() => _photoIndex = index),
              ),
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _ListingHeader(detail: detail),
                    if (detail.description.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      _SectionCard(
                        title: 'About this property',
                        child: Text(detail.description),
                      ),
                    ],
                    const SizedBox(height: 16),
                    _SectionCard(
                      title: 'Pricing overview',
                      child: _PricingOverview(detail: detail),
                    ),
                    const SizedBox(height: 16),
                    _SectionCard(
                      title: 'Stay period',
                      child: _PeriodSelector(
                        selectedPeriod: selectedPeriod,
                        onPickDates: () => _pickDateRange(selectedPeriod),
                        onClear: selectedPeriod.isComplete
                            ? () => ref
                                .read(
                                  listingSelectedPeriodProvider(
                                          widget.listingId)
                                      .notifier,
                                )
                                .state = const ListingDateRange()
                            : null,
                      ),
                    ),
                    const SizedBox(height: 16),
                    _SectionCard(
                      title: 'Availability',
                      child: _AvailabilityPanel(
                        availabilityAsync: availabilityAsync,
                        selectedPeriod: selectedPeriod,
                        onRetry: () => ref.invalidate(
                          listingAvailabilityProvider((
                            listingId: widget.listingId,
                            period: selectedPeriod,
                          )),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                     _SectionCard(
                       title: 'Quote for selected period',
                       child: _PricingQuotePanel(
                         quoteAsync: quoteAsync,
                        selectedPeriod: selectedPeriod,
                        onRetry: () => ref.invalidate(
                          listingPricingQuoteProvider((
                            listingId: widget.listingId,
                            period: selectedPeriod,
                          )),
                        ),
                       ),
                     ),
                    const SizedBox(height: 16),
                    _SectionCard(
                      title: 'Request this stay',
                      child: _ApplicationRequestPanel(
                        listingId: widget.listingId,
                        listingTitle: detail.title,
                        selectedPeriod: selectedPeriod,
                        quoteAsync: quoteAsync,
                      ),
                    ),
                    if (detail.attributes.isNotEmpty ||
                        detail.amenities.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      _SectionCard(
                        title: 'Amenities & details',
                        child: _DetailsWrap(detail: detail),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ListingGallery extends StatelessWidget {
  final List<ListingPhoto> photos;
  final int currentIndex;
  final ValueChanged<int> onPageChanged;

  const _ListingGallery({
    required this.photos,
    required this.currentIndex,
    required this.onPageChanged,
  });

  @override
  Widget build(BuildContext context) {
    if (photos.isEmpty) {
      return Container(
        height: 240,
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        alignment: Alignment.center,
        child: const Icon(Icons.home_work_outlined, size: 64),
      );
    }

    return Stack(
      alignment: Alignment.bottomCenter,
      children: [
        SizedBox(
          height: 240,
          child: PageView.builder(
            itemCount: photos.length,
            onPageChanged: onPageChanged,
            itemBuilder: (context, index) {
              final photo = photos[index];
              return CachedNetworkImage(
                imageUrl: photo.url,
                fit: BoxFit.cover,
                errorWidget: (_, __, ___) => Container(
                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                  child: const Icon(Icons.broken_image_outlined, size: 40),
                ),
                placeholder: (_, __) => Container(
                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                  child: const Center(
                    child: CircularProgressIndicator.adaptive(),
                  ),
                ),
              );
            },
          ),
        ),
        if (photos.length > 1)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                for (var index = 0; index < photos.length; index++)
                  Container(
                    margin: const EdgeInsets.symmetric(horizontal: 3),
                    height: 8,
                    width: 8,
                    decoration: BoxDecoration(
                      color: currentIndex == index
                          ? Colors.white
                          : Colors.white.withValues(alpha: 0.4),
                      shape: BoxShape.circle,
                    ),
                  ),
              ],
            ),
          ),
      ],
    );
  }
}

class _ListingHeader extends StatelessWidget {
  final ListingDetail detail;

  const _ListingHeader({required this.detail});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            if (detail.category != null)
              Chip(
                avatar: const Icon(Icons.apartment_outlined, size: 16),
                label: Text(detail.category!.name),
              ),
            Chip(
              avatar: Icon(
                detail.isPublished
                    ? Icons.public_outlined
                    : Icons.edit_outlined,
                size: 16,
              ),
              label: Text(detail.isPublished ? 'Published' : detail.status),
            ),
            if (detail.instantBookingEnabled)
              const Chip(
                avatar: Icon(Icons.flash_on_outlined, size: 16),
                label: Text('Instant booking'),
              ),
          ],
        ),
        const SizedBox(height: 12),
        Text(
          detail.title,
          style: theme.textTheme.headlineSmall
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.location_on_outlined, size: 18),
            const SizedBox(width: 6),
            Expanded(child: Text(detail.locationAddress)),
          ],
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            _InfoTile(
              icon: Icons.payments_outlined,
              label: 'Starting price',
              value: detail.pricePreview.displayLabel,
            ),
            if (detail.depositAmount != null)
              _InfoTile(
                icon: Icons.savings_outlined,
                label: 'Security deposit',
                value: 'NPR ${detail.depositAmount!.toStringAsFixed(0)}',
              ),
            if (detail.averageRating != null)
              _InfoTile(
                icon: Icons.star_outline,
                label: 'Rating',
                value:
                    '${detail.averageRating!.toStringAsFixed(1)} · ${detail.reviewCount} review${detail.reviewCount == 1 ? '' : 's'}',
              ),
          ],
        ),
      ],
    );
  }
}

class _PricingOverview extends StatelessWidget {
  final ListingDetail detail;

  const _PricingOverview({required this.detail});

  @override
  Widget build(BuildContext context) {
    final rows = <_PriceRowData>[
      if (detail.pricingOverview.dailyRate != null)
        _PriceRowData('Daily', detail.pricingOverview.dailyRate!),
      if (detail.pricingOverview.weeklyRate != null)
        _PriceRowData('Weekly', detail.pricingOverview.weeklyRate!),
      if (detail.pricingOverview.monthlyRate != null)
        _PriceRowData('Monthly', detail.pricingOverview.monthlyRate!),
    ];

    if (rows.isEmpty) {
      return Text(
        detail.pricePreview.displayLabel,
        style: Theme.of(context)
            .textTheme
            .titleMedium
            ?.copyWith(fontWeight: FontWeight.bold),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final row in rows)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: _AmountRow(
              label: row.label,
              amount: row.amount,
              currency: detail.pricingOverview.currency,
            ),
          ),
        if (detail.pricingOverview.summary != null &&
            detail.pricingOverview.summary!.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(detail.pricingOverview.summary!),
        ],
      ],
    );
  }
}

class _PeriodSelector extends StatelessWidget {
  final ListingDateRange selectedPeriod;
  final VoidCallback onPickDates;
  final VoidCallback? onClear;

  const _PeriodSelector({
    required this.selectedPeriod,
    required this.onPickDates,
    this.onClear,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          selectedPeriod.isComplete
              ? '${selectedPeriod.label} · ${selectedPeriod.totalDays} day${selectedPeriod.totalDays == 1 ? '' : 's'}'
              : 'Select a period to fetch live availability and pricing.',
          style: theme.textTheme.bodyMedium,
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: onPickDates,
                icon: const Icon(Icons.calendar_today_outlined),
                label: Text(selectedPeriod.isComplete
                    ? 'Change dates'
                    : 'Select dates'),
              ),
            ),
            if (onClear != null) ...[
              const SizedBox(width: 12),
              TextButton(
                onPressed: onClear,
                child: const Text('Clear'),
              ),
            ],
          ],
        ),
      ],
    );
  }
}

class _AvailabilityPanel extends StatelessWidget {
  final AsyncValue<ListingAvailability?> availabilityAsync;
  final ListingDateRange selectedPeriod;
  final VoidCallback onRetry;

  const _AvailabilityPanel({
    required this.availabilityAsync,
    required this.selectedPeriod,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    if (!selectedPeriod.isComplete) {
      return const Text('Choose dates to check calendar availability.');
    }

    return availabilityAsync.when(
      loading: () => const Padding(
        padding: EdgeInsets.symmetric(vertical: 8),
        child: Center(child: CircularProgressIndicator.adaptive()),
      ),
      error: (error, _) => _InlineError(
        message: ErrorHandler.handle(error).message,
        onRetry: onRetry,
      ),
      data: (availability) {
        if (availability == null) {
          return const Text('Choose dates to check calendar availability.');
        }

        final dateFormatter = DateFormat('MMM d, y');
        final theme = Theme.of(context);

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: availability.isAvailable
                    ? Colors.green.withValues(alpha: 0.08)
                    : theme.colorScheme.error.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: availability.isAvailable
                      ? Colors.green.withValues(alpha: 0.4)
                      : theme.colorScheme.error.withValues(alpha: 0.3),
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    availability.isAvailable
                        ? Icons.check_circle_outline
                        : Icons.event_busy_outlined,
                    color: availability.isAvailable
                        ? Colors.green
                        : theme.colorScheme.error,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      availability.isAvailable
                          ? 'This property is available for the selected period.'
                          : availability.note?.isNotEmpty == true
                              ? availability.note!
                              : 'The selected dates are not currently available.',
                    ),
                  ),
                ],
              ),
            ),
            if (!availability.isAvailable &&
                availability.nextAvailableStart != null) ...[
              const SizedBox(height: 12),
              Text(
                'Next opening: ${dateFormatter.format(availability.nextAvailableStart!.toLocal())}',
                style: theme.textTheme.bodyMedium,
              ),
            ],
            if (availability.blockedPeriods.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                'Blocked periods',
                style: theme.textTheme.titleSmall
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              for (final block in availability.blockedPeriods)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      color: theme.colorScheme.surfaceContainerHighest,
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.block_outlined, size: 18),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            '${block.reason.isNotEmpty ? block.reason : 'Blocked'} · ${_dateRangeLabel(block, dateFormatter)}',
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ],
        );
      },
    );
  }

  String _dateRangeLabel(AvailabilityBlock block, DateFormat formatter) {
    if (block.startAt == null && block.endAt == null) {
      return 'Dates unavailable';
    }
    if (block.startAt != null && block.endAt != null) {
      return '${formatter.format(block.startAt!.toLocal())} – ${formatter.format(block.endAt!.toLocal())}';
    }
    final date = block.startAt ?? block.endAt!;
    return formatter.format(date.toLocal());
  }
}

class _PricingQuotePanel extends StatelessWidget {
  final AsyncValue<PricingQuote?> quoteAsync;
  final ListingDateRange selectedPeriod;
  final VoidCallback onRetry;

  const _PricingQuotePanel({
    required this.quoteAsync,
    required this.selectedPeriod,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    if (!selectedPeriod.isComplete) {
      return const Text('Choose dates to calculate a rental quote.');
    }

    return quoteAsync.when(
      loading: () => const Padding(
        padding: EdgeInsets.symmetric(vertical: 8),
        child: Center(child: CircularProgressIndicator.adaptive()),
      ),
      error: (error, _) => _InlineError(
        message: ErrorHandler.handle(error).message,
        onRetry: onRetry,
      ),
      data: (quote) {
        if (quote == null) {
          return const Text('Choose dates to calculate a rental quote.');
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (quote.rateLabel != null && quote.rateLabel!.isNotEmpty) ...[
              Text(
                quote.rateLabel!,
                style: Theme.of(context)
                    .textTheme
                    .titleSmall
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
            ],
            for (final item in quote.lineItems)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: _AmountRow(
                  label: item.label,
                  amount: item.amount,
                  currency: quote.currency,
                ),
              ),
            const Divider(height: 24),
            _AmountRow(
              label: 'Quoted total',
              amount: quote.totalFee,
              currency: quote.currency,
              emphasize: true,
            ),
            if (quote.totalDueNow != quote.totalFee)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: _AmountRow(
                  label: 'Due now',
                  amount: quote.totalDueNow,
                  currency: quote.currency,
                  emphasize: true,
                ),
              ),
            if (quote.note != null && quote.note!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(quote.note!),
            ],
          ],
        );
      },
    );
  }
}

class _DetailsWrap extends StatelessWidget {
  final ListingDetail detail;

  const _DetailsWrap({required this.detail});

  @override
  Widget build(BuildContext context) {
    final chips = <Widget>[
      ...detail.amenities.map(
        (amenity) => Chip(
          avatar: const Icon(Icons.check_circle_outline, size: 16),
          label: Text(amenity),
        ),
      ),
      ...detail.attributes.take(8).map(
            (attribute) =>
                Chip(label: Text('${attribute.label}: ${attribute.value}')),
          ),
    ];

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: chips,
    );
  }
}

class _SectionCard extends StatelessWidget {
  final String title;
  final Widget child;

  const _SectionCard({
    required this.title,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }
}

class _InlineError extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _InlineError({
    required this.message,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          message,
          style: TextStyle(color: Theme.of(context).colorScheme.error),
        ),
        const SizedBox(height: 8),
        TextButton(
          onPressed: onRetry,
          child: const Text('Retry'),
        ),
      ],
    );
  }
}

class _ApplicationRequestPanel extends ConsumerStatefulWidget {
  final String listingId;
  final String listingTitle;
  final ListingDateRange selectedPeriod;
  final AsyncValue<PricingQuote?> quoteAsync;

  const _ApplicationRequestPanel({
    required this.listingId,
    required this.listingTitle,
    required this.selectedPeriod,
    required this.quoteAsync,
  });

  @override
  ConsumerState<_ApplicationRequestPanel> createState() =>
      _ApplicationRequestPanelState();
}

class _ApplicationRequestPanelState
    extends ConsumerState<_ApplicationRequestPanel> {
  final _specialRequestsController = TextEditingController();
  String? _selectedPaymentProvider;
  bool _submitting = false;

  @override
  void dispose() {
    _specialRequestsController.dispose();
    super.dispose();
  }

  Future<void> _submitApplication({
    required PricingQuote quote,
    required String paymentMethodId,
  }) async {
    if (!widget.selectedPeriod.isComplete) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Select dates before requesting this stay.'),
        ),
      );
      return;
    }

    setState(() => _submitting = true);
    try {
      final booking = await ref.read(bookingRepositoryProvider).createBooking(
            CreateBookingRequest(
              propertyId: widget.listingId,
              rentalStartAt: widget.selectedPeriod.start!,
              rentalEndAt: widget.selectedPeriod.end!,
              specialRequests: _specialRequestsController.text.trim(),
              paymentMethodId: paymentMethodId,
              idempotencyKey:
                  'mobile-${widget.listingId}-${DateTime.now().millisecondsSinceEpoch}',
            ),
          );
      ref.invalidate(bookingsProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Application submitted for ${widget.listingTitle}.',
          ),
        ),
      );
      context.push(AppConstants.applicationDetailRoute(booking.id));
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(ErrorHandler.handle(error).message),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final canSubmit = ref.watch(canSubmitApplicationsProvider);
    final paymentProvidersAsync = ref.watch(paymentProvidersProvider);

    if (!canSubmit) {
      return const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline),
          SizedBox(width: 12),
          Expanded(
            child: Text(
              'Stay requests and lease signing on mobile are designed for tenant accounts. Manager and landlord workflows stay on the website.',
            ),
          ),
        ],
      );
    }

    if (!widget.selectedPeriod.isComplete) {
      return const Text(
        'Choose your stay dates above to unlock the booking request form.',
      );
    }

    return widget.quoteAsync.when(
      loading: () => const Padding(
        padding: EdgeInsets.symmetric(vertical: 8),
        child: Center(child: CircularProgressIndicator.adaptive()),
      ),
      error: (error, _) => _InlineError(
        message: ErrorHandler.handle(error).message,
        onRetry: () {
          ref.invalidate(
            listingPricingQuoteProvider((
              listingId: widget.listingId,
              period: widget.selectedPeriod,
            )),
          );
        },
      ),
      data: (quote) {
        if (quote == null) {
          return const Text(
            'A pricing quote is required before you can submit an application.',
          );
        }

        return paymentProvidersAsync.when(
          loading: () => const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: Center(child: CircularProgressIndicator.adaptive()),
          ),
          error: (error, _) => Text(
            ErrorHandler.handle(error).message,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
          data: (providers) {
            final availableProviders = providers.isNotEmpty
                ? providers
                : const <String>['manual_review'];
            final selectedProvider =
                availableProviders.contains(_selectedPaymentProvider) &&
                        _selectedPaymentProvider != null
                    ? _selectedPaymentProvider!
                    : availableProviders.first;

            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${widget.selectedPeriod.label} · ${widget.selectedPeriod.totalDays} day${widget.selectedPeriod.totalDays == 1 ? '' : 's'}',
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Theme.of(context)
                        .colorScheme
                        .surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    children: [
                      _AmountRow(
                        label: 'Due now',
                        amount: quote.totalDueNow,
                        currency: quote.currency,
                        emphasize: true,
                      ),
                      if (quote.depositAmount != 0) ...[
                        const SizedBox(height: 8),
                        _AmountRow(
                          label: 'Security deposit',
                          amount: quote.depositAmount,
                          currency: quote.currency,
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  key: ValueKey(selectedProvider),
                  initialValue: selectedProvider,
                  decoration: const InputDecoration(
                    labelText: 'Payment method',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.account_balance_wallet_outlined),
                  ),
                  items: availableProviders
                      .map(
                        (provider) => DropdownMenuItem<String>(
                          value: provider,
                          child: Text(_humanizeProvider(provider)),
                        ),
                      )
                      .toList(),
                  onChanged: _submitting
                      ? null
                      : (value) =>
                          setState(() => _selectedPaymentProvider = value),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _specialRequestsController,
                  minLines: 3,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    labelText: 'Special requests',
                    hintText:
                        'Move-in notes, furnishing requests, or other context',
                    border: OutlineInputBorder(),
                    alignLabelWithHint: true,
                  ),
                ),
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: _submitting
                      ? null
                      : () => _submitApplication(
                            quote: quote,
                            paymentMethodId: selectedProvider,
                          ),
                  icon: _submitting
                      ? const SizedBox(
                          height: 18,
                          width: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send_outlined),
                  label: Text(
                    'Submit request · ${_formatCurrency(quote.totalDueNow, quote.currency)}',
                  ),
                ),
              ],
            );
          },
        );
      },
    );
  }

  String _humanizeProvider(String value) {
    return value
        .replaceAll(RegExp(r'[_-]+'), ' ')
        .split(' ')
        .where((part) => part.isNotEmpty)
        .map((part) => '${part[0].toUpperCase()}${part.substring(1)}')
        .join(' ');
  }
}

String _formatCurrency(double amount, String currency) {
  final rounded = amount % 1 == 0 ? amount.toStringAsFixed(0) : amount.toStringAsFixed(2);
  return '$currency $rounded';
}

class _AmountRow extends StatelessWidget {
  final String label;
  final double amount;
  final String currency;
  final bool emphasize;

  const _AmountRow({
    required this.label,
    required this.amount,
    required this.currency,
    this.emphasize = false,
  });

  @override
  Widget build(BuildContext context) {
    final style = emphasize
        ? Theme.of(context)
            .textTheme
            .titleSmall
            ?.copyWith(fontWeight: FontWeight.bold)
        : Theme.of(context).textTheme.bodyMedium;

    return Row(
      children: [
        Expanded(child: Text(label, style: style)),
        Text(
          '$currency ${amount % 1 == 0 ? amount.toStringAsFixed(0) : amount.toStringAsFixed(2)}',
          style: style,
        ),
      ],
    );
  }
}

class _InfoTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoTile({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minWidth: 180),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 18),
          const SizedBox(width: 10),
          Flexible(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: Theme.of(context).textTheme.bodySmall),
                Text(
                  value,
                  style: Theme.of(context)
                      .textTheme
                      .bodyMedium
                      ?.copyWith(fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _PriceRowData {
  final String label;
  final double amount;

  const _PriceRowData(this.label, this.amount);
}

class _DetailErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _DetailErrorState({
    required this.message,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
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
