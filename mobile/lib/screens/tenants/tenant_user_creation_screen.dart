/// Screen to create a user account for a new tenant.
///
/// This is the first step in the "Add Tenant" flow.
/// Implements Owner-driven tenant account creation.
library;

import 'package:flutter/material.dart';

import '../../config/app_router.dart';
import '../../config/constants.dart';
import '../../models/property.dart';
import '../../screens/auth/login_screen.dart'; // Using LoginScreen style
import '../../services/api_service.dart';

class TenantUserCreationScreen extends StatefulWidget {
  const TenantUserCreationScreen({
    super.key,
    this.propertyId,
  });

  final String? propertyId;

  @override
  State<TenantUserCreationScreen> createState() =>
      _TenantUserCreationScreenState();
}

class _TenantUserCreationScreenState extends State<TenantUserCreationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _fullNameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  
  bool _isLoading = false;
  bool _isPasswordVisible = false;
  
  // Property selection if not provided
  String? _selectedPropertyId;
  List<Property> _properties = [];
  bool _isLoadingProperties = false;

  @override
  void initState() {
    super.initState();
    _selectedPropertyId = widget.propertyId;
    if (_selectedPropertyId == null) {
      _loadProperties();
    }
  }

  @override
  void dispose() {
    _emailController.dispose();
    _fullNameController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _loadProperties() async {
    setState(() => _isLoadingProperties = true);
    try {
      // Assuming GET /api/v1/properties returns list for Owner
      final response = await ApiService.instance.get('/api/v1/properties');
      if (response.isSuccess && response.data != null) {
        final data = response.data['data'] as List;
        setState(() {
          _properties = data
              .map((json) => Property.fromJson(json))
              .toList();
          
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

  Future<void> _handleCreateUser() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedPropertyId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a property')),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      // Call create user endpoint
      // Note: We are logged in as Owner, effectively creating a Tenant User
      final response = await ApiService.instance.post(
        '/api/v1/users',
        data: {
          'email': _emailController.text.trim(),
          'password': _passwordController.text,
          'full_name': _fullNameController.text.trim(),
          'phone': _phoneController.text.trim(),
          'role': 'tenant', // Explicitly creating a tenant
        },
      );

      if (!mounted) return;

      if (response.isSuccess) {
        final userId = response.data['data']['id'];
        
        // Navigate to Step 2: Tenant Record Creation
        // We pass the new userId and the selected propertyId
        Navigator.pushNamed(
          context,
          '/tenants/record-create', // New route for TenantFormScreen
          arguments: {
            'userId': userId,
            'propertyId': _selectedPropertyId,
          },
        ).then((result) {
          if (result == true) {
            Navigator.pop(context, true); // Success, go back to list
          }
        });
      } else {
         ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response.message ?? 'Failed to create user'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
       ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add Tenant - Step 1/2')),
      body: _isLoadingProperties
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      'Create Tenant Account',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'First, create a user account for the tenant. They will use these credentials to log in.',
                      style: TextStyle(color: Colors.grey),
                    ),
                    const SizedBox(height: 24),
                    
                    // Property Selection
                    if (widget.propertyId == null) ...[
                      DropdownButtonFormField<String>(
                        value: _selectedPropertyId,
                        decoration: const InputDecoration(
                          labelText: 'Select Property',
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
                    ],

                    TextFormField(
                      controller: _fullNameController,
                      decoration: const InputDecoration(
                        labelText: 'Full Name',
                        prefixIcon: Icon(Icons.person),
                      ),
                      validator: (val) =>
                          val?.isEmpty == true ? 'Name is required' : null,
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _emailController,
                      decoration: const InputDecoration(
                        labelText: 'Email Address',
                        prefixIcon: Icon(Icons.email),
                      ),
                      keyboardType: TextInputType.emailAddress,
                      validator: (val) {
                        if (val?.isEmpty == true) return 'Email is required';
                        if (!val!.contains('@')) return 'Invalid email';
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _phoneController,
                      decoration: const InputDecoration(
                        labelText: 'Phone Number',
                        prefixIcon: Icon(Icons.phone),
                      ),
                      keyboardType: TextInputType.phone,
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _passwordController,
                      obscureText: !_isPasswordVisible,
                      decoration: InputDecoration(
                        labelText: 'Password',
                        prefixIcon: const Icon(Icons.lock),
                        suffixIcon: IconButton(
                          icon: Icon(_isPasswordVisible
                              ? Icons.visibility_off
                              : Icons.visibility),
                          onPressed: () {
                            setState(() =>
                                _isPasswordVisible = !_isPasswordVisible);
                          },
                        ),
                      ),
                      validator: (val) =>
                          (val?.length ?? 0) < 8 ? 'Min 8 characters' : null,
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: _isLoading ? null : _handleCreateUser,
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                      child: _isLoading
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text('Next: Set Tenancy Details'),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
