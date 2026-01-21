/// Screen to create or edit a maintenance request.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/maintenance_provider.dart';
import '../../providers/property_provider.dart';
import '../../models/maintenance_request.dart';
import '../../models/property.dart';

class MaintenanceFormScreen extends StatefulWidget {
  const MaintenanceFormScreen({super.key});

  @override
  State<MaintenanceFormScreen> createState() => _MaintenanceFormScreenState();
}

class _MaintenanceFormScreenState extends State<MaintenanceFormScreen> {
  final _formKey = GlobalKey<FormState>();
  
  // Controllers
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  
  // State
  MaintenancePriority _priority = MaintenancePriority.medium;
  String? _selectedPropertyId;
  List<Property> _properties = [];
  bool _isLoadingProperties = false;

  @override
  void initState() {
    super.initState();
    _loadProperties();
  }
  
  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _loadProperties() async {
    setState(() => _isLoadingProperties = true);
    // Ideally use PropertyProvider if available and loaded
    // Or load fresh list for "My Properties" / "Tenancy Properties"
    // Since we don't have a dedicated "My Properties" for generic usage easily exposed in this context without role check,
    // let's assume we can fetch associated properties.
    // For simplicity, we'll try to use PropertyProvider or fetch from API.
    // Assuming PropertyProvider exists and handles this.
    try {
        // Quick fetch: use ApiService directly or assume PropertyProvider has loaded
        // Let's assume user has properties (Owner/Tenant).
        // Since we are creating a generic form, we need to know user context. 
        // For now, let's fetch '/api/v1/properties' which returns appropriate list for user role
        // But we don't have direct access to ApiService here easily without Provider or import.
        final provider = context.read<PropertyProvider>();
        await provider.loadProperties();
        if (mounted) {
          setState(() {
            _properties = provider.properties;
            if (_properties.isNotEmpty) {
              _selectedPropertyId = _properties.first.id;
            }
          });
        }
    } catch (e) {
      // Handle error
    } finally {
      if (mounted) setState(() => _isLoadingProperties = false);
    }
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedPropertyId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a property')),
      );
      return;
    }

    final success = await context.read<MaintenanceProvider>().createRequest(
      propertyId: _selectedPropertyId!,
      title: _titleController.text.trim(),
      description: _descriptionController.text.trim(),
      priority: _priority,
      // images: [] // TODO: Image upload
    );

    if (success && mounted) {
      Navigator.pop(context, true);
    } else if (mounted) {
       ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to submit request')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('New Maintenance Request')),
      body: _isLoadingProperties
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Property Dropdown
                    DropdownButtonFormField<String>(
                      value: _selectedPropertyId,
                      decoration: const InputDecoration(
                        labelText: 'Property',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.home),
                      ),
                      items: _properties.map((p) {
                         return DropdownMenuItem(
                           value: p.id,
                           child: Text(p.name, overflow: TextOverflow.ellipsis),
                         );
                      }).toList(),
                      onChanged: (val) => setState(() => _selectedPropertyId = val),
                      validator: (val) => val == null ? 'Required' : null,
                    ),
                    const SizedBox(height: 16),
                    
                    // Title
                    TextFormField(
                      controller: _titleController,
                      decoration: const InputDecoration(
                        labelText: 'Title',
                        hintText: 'e.g., Leaking Faucet',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.title),
                      ),
                      validator: (val) => val?.isEmpty == true ? 'Required' : null,
                    ),
                    const SizedBox(height: 16),
                    
                    // Priority
                    DropdownButtonFormField<MaintenancePriority>(
                      value: _priority,
                      decoration: const InputDecoration(
                        labelText: 'Priority',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.flag),
                      ),
                      items: MaintenancePriority.values.map((p) {
                        return DropdownMenuItem(
                          value: p,
                          child: Text(p.label),
                        );
                      }).toList(),
                      onChanged: (val) {
                        if (val != null) setState(() => _priority = val);
                      },
                    ),
                    const SizedBox(height: 16),
                    
                    // Description
                    TextFormField(
                      controller: _descriptionController,
                      decoration: const InputDecoration(
                        labelText: 'Description',
                        hintText: 'Describe the issue in detail...',
                        border: OutlineInputBorder(),
                        alignLabelWithHint: true,
                        prefixIcon: Icon(Icons.description),
                      ),
                      maxLines: 5,
                      validator: (val) => val?.isEmpty == true ? 'Required' : null,
                    ),
                    const SizedBox(height: 24),
                    
                    // Submit Button
                    Consumer<MaintenanceProvider>(
                      builder: (context, provider, child) {
                        return ElevatedButton(
                          onPressed: provider.isLoading ? null : _handleSubmit,
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 16),
                          ),
                          child: provider.isLoading 
                              ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                              : const Text('Submit Request'),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
