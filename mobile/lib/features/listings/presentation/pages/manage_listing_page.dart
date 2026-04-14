import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/error/error_handler.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_snackbar.dart';
import '../../../../shared/widgets/loading_button.dart';
import '../../data/models/create_listing_request.dart';
import '../../data/models/listing_category.dart';
import '../providers/listing_provider.dart';

class ManageListingPage extends ConsumerStatefulWidget {
  const ManageListingPage({super.key});

  @override
  ConsumerState<ManageListingPage> createState() => _ManageListingPageState();
}

class _ManageListingPageState extends ConsumerState<ManageListingPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _addressController = TextEditingController();
  final _depositController = TextEditingController();
  final _minDurationController = TextEditingController();
  final _maxDurationController = TextEditingController();

  bool _instantBookingEnabled = false;
  bool _saving = false;
  String? _selectedCategoryId;

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    _addressController.dispose();
    _depositController.dispose();
    _minDurationController.dispose();
    _maxDurationController.dispose();
    super.dispose();
  }

  double? _parseDouble(String value) {
    final trimmed = value.trim();
    if (trimmed.isEmpty) return null;
    return double.tryParse(trimmed);
  }

  int? _parseInt(String value) {
    final trimmed = value.trim();
    if (trimmed.isEmpty) return null;
    return int.tryParse(trimmed);
  }

  ListingCategory? _findCategoryById(
      List<ListingCategory> categories, String? id) {
    if (id == null || id.isEmpty) return null;
    for (final category in categories) {
      if (category.id == id) return category;
    }
    return null;
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    final categories =
        ref.read(listingCategoriesProvider).valueOrNull ?? const [];
    final category = _findCategoryById(categories, _selectedCategoryId);
    if (category == null) {
      showErrorSnackbar(context, 'Choose a property type for this draft.');
      return;
    }

    setState(() => _saving = true);

    try {
      final request = CreateListingRequest(
        propertyTypeId: category.id,
        name: _nameController.text.trim(),
        description: _descriptionController.text.trim(),
        locationAddress: _addressController.text.trim(),
        depositAmount: _parseDouble(_depositController.text),
        minRentalDurationHours: _parseInt(_minDurationController.text),
        maxRentalDurationDays: _parseInt(_maxDurationController.text),
        instantBookingEnabled: _instantBookingEnabled,
      );

      final listing = await ref
          .read(listingsRepositoryProvider)
          .createListingDraft(request);

      ref.invalidate(listingSearchResultsProvider);

      if (!mounted) return;

      showSuccessSnackbar(context, 'Draft listing created.');
      if (listing.id.isNotEmpty) {
        context.go(AppConstants.listingDetailRoute(listing.id));
      } else {
        context.pop();
      }
    } catch (error) {
      if (!mounted) return;
      showErrorSnackbar(context, ErrorHandler.handle(error).message);
    } finally {
      if (mounted) {
        setState(() => _saving = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final canManage = ref.watch(canManageListingsProvider);
    final categoriesAsync = ref.watch(listingCategoriesProvider);
    final selectedCategoryAsync =
        _selectedCategoryId == null || _selectedCategoryId!.isEmpty
            ? null
            : ref.watch(listingCategoryDetailProvider(_selectedCategoryId!));

    return Scaffold(
      appBar: AppBar(title: const Text('Manage listings')),
      body: !canManage
          ? const _ManageAccessDenied()
          : categoriesAsync.when(
              loading: () =>
                  const Center(child: CircularProgressIndicator.adaptive()),
              error: (error, _) => _ManageErrorState(
                message: ErrorHandler.handle(error).message,
                onRetry: () => ref.invalidate(listingCategoriesProvider),
              ),
              data: (categories) => ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  const _DraftListingIntro(),
                  const SizedBox(height: 16),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Form(
                        key: _formKey,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Create draft listing',
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 16),
                            DropdownButtonFormField<String?>(
                              key: ValueKey(_selectedCategoryId),
                              initialValue: _selectedCategoryId,
                              decoration: const InputDecoration(
                                labelText: 'Property type',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.apartment_outlined),
                              ),
                              items: categories
                                  .map(
                                    (category) => DropdownMenuItem<String?>(
                                      value: category.id,
                                      child: Text(category.name),
                                    ),
                                  )
                                  .toList(),
                              onChanged: (value) =>
                                  setState(() => _selectedCategoryId = value),
                              validator: (value) {
                                if (value == null || value.isEmpty) {
                                  return 'Required';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: 12),
                            AppTextField(
                              controller: _nameController,
                              label: 'Listing title',
                              prefixIcon: Icons.home_work_outlined,
                              validator: (value) {
                                if (value == null || value.trim().isEmpty) {
                                  return 'Required';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: 12),
                            AppTextField(
                              controller: _addressController,
                              label: 'Address / area',
                              prefixIcon: Icons.location_on_outlined,
                              validator: (value) {
                                if (value == null || value.trim().isEmpty) {
                                  return 'Required';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: 12),
                            AppTextField(
                              controller: _descriptionController,
                              label: 'Description',
                              prefixIcon: Icons.notes_outlined,
                              maxLines: 4,
                              validator: (value) {
                                if (value == null || value.trim().isEmpty) {
                                  return 'Required';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                Expanded(
                                  child: AppTextField(
                                    controller: _depositController,
                                    label: 'Security deposit',
                                    prefixIcon: Icons.savings_outlined,
                                    keyboardType:
                                        const TextInputType.numberWithOptions(
                                      decimal: true,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: AppTextField(
                                    controller: _minDurationController,
                                    label: 'Min hours',
                                    prefixIcon: Icons.timer_outlined,
                                    keyboardType: TextInputType.number,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: AppTextField(
                                    controller: _maxDurationController,
                                    label: 'Max days',
                                    prefixIcon: Icons.event_outlined,
                                    keyboardType: TextInputType.number,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            SwitchListTile(
                              value: _instantBookingEnabled,
                              title: const Text('Enable instant booking'),
                              subtitle: const Text(
                                'Useful for high-confidence inventory. Publishing controls will follow in a later landlord slice.',
                              ),
                              contentPadding: EdgeInsets.zero,
                              onChanged: (value) => setState(
                                () => _instantBookingEnabled = value,
                              ),
                            ),
                            const SizedBox(height: 12),
                            LoadingButton(
                              isLoading: _saving,
                              onPressed: _submit,
                              label: 'Create draft',
                              icon: Icons.add_home_work_outlined,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  if (selectedCategoryAsync != null) ...[
                    const SizedBox(height: 16),
                    selectedCategoryAsync.when(
                      data: (category) =>
                          _CategoryDetailsCard(category: category),
                      loading: () => const Card(
                        child: Padding(
                          padding: EdgeInsets.all(16),
                          child: LinearProgressIndicator(),
                        ),
                      ),
                      error: (error, _) => Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Text(
                            'Could not load category attributes: ${ErrorHandler.handle(error).message}',
                          ),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
    );
  }
}

class _DraftListingIntro extends StatelessWidget {
  const _DraftListingIntro();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Landlord extension point',
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'This mobile slice prioritizes tenant discovery. Draft creation is included as a lightweight landlord starting point, while media uploads, advanced attributes, pricing rule authoring, and publish/unpublish controls can extend this route later without reworking navigation.',
            ),
          ],
        ),
      ),
    );
  }
}

class _CategoryDetailsCard extends StatelessWidget {
  final ListingCategory category;

  const _CategoryDetailsCard({required this.category});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Category attributes',
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            if (category.attributes.isEmpty)
              const Text(
                'No additional attributes were returned for this category yet.',
              )
            else
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final attribute in category.attributes)
                    Chip(
                      label: Text(
                        attribute.isRequired
                            ? '${attribute.name} *'
                            : attribute.name,
                      ),
                    ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

class _ManageAccessDenied extends StatelessWidget {
  const _ManageAccessDenied();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.lock_outline, size: 48),
            SizedBox(height: 12),
            Text(
              'Only landlord or admin accounts can create listing drafts from this screen.',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _ManageErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ManageErrorState({
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
