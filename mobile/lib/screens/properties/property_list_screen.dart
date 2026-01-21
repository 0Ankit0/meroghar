/// Property list screen for displaying all properties.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/property_provider.dart';
import '../../models/property.dart';
import 'property_form_screen.dart';

class PropertyListScreen extends StatefulWidget {
  const PropertyListScreen({super.key});

  @override
  State<PropertyListScreen> createState() => _PropertyListScreenState();
}

class _PropertyListScreenState extends State<PropertyListScreen> {
  @override
  void initState() {
    super.initState();
    // Load properties when screen initializes
    Future.microtask(() {
      context.read<PropertyProvider>().loadProperties();
    });
  }

  Future<void> _refreshProperties() async {
    await context.read<PropertyProvider>().loadProperties();
  }

  Future<void> _navigateToAddProperty() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const PropertyFormScreen()),
    );

    if (result == true) {
      _refreshProperties();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Properties'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: _navigateToAddProperty,
            tooltip: 'Add Property',
          ),
        ],
      ),
      body: Consumer<PropertyProvider>(
        builder: (context, propertyProvider, child) {
          if (propertyProvider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (propertyProvider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, size: 64, color: Colors.red[300]),
                  const SizedBox(height: 16),
                  Text(
                    propertyProvider.error!,
                    style: Theme.of(context).textTheme.bodyLarge,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: _refreshProperties,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          if (propertyProvider.properties.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.home_work_outlined,
                      size: 80, color: Colors.grey[400]),
                  const SizedBox(height: 16),
                  Text(
                    'No Properties Found',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Add your first property to get started',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.grey[600],
                        ),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    onPressed: _navigateToAddProperty,
                    icon: const Icon(Icons.add),
                    label: const Text('Add Property'),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: _refreshProperties,
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: propertyProvider.properties.length,
              itemBuilder: (context, index) {
                final property = propertyProvider.properties[index];
                return _PropertyCard(
                  property: property,
                  onTap: () {
                    propertyProvider.selectProperty(property);
                    // Navigate to property details
                  },
                );
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _navigateToAddProperty,
        child: const Icon(Icons.add),
      ),
    );
  }
}

class _PropertyCard extends StatelessWidget {
  final Property property;
  final VoidCallback onTap;

  const _PropertyCard({
    required this.property,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.home_work, color: Colors.blue, size: 32),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          property.name,
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${property.addressLine1}, ${property.city}',
                          style:
                              Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: Colors.grey[600],
                                  ),
                        ),
                      ],
                    ),
                  ),
                  Icon(Icons.chevron_right, color: Colors.grey[400]),
                ],
              ),
              const SizedBox(height: 12),
              const Divider(),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _InfoChip(
                    icon: Icons.apartment,
                    label: '${property.totalUnits} Units',
                  ),
                  _InfoChip(
                    icon: Icons.currency_exchange,
                    label: property.baseCurrency,
                  ),
                  if (property.city.isNotEmpty)
                    _InfoChip(
                      icon: Icons.location_city,
                      label: property.city,
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;

  const _InfoChip({
    required this.icon,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 16, color: Colors.grey[600]),
        const SizedBox(width: 4),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.grey[600],
              ),
        ),
      ],
    );
  }
}
