/// Home screen with bottom navigation for main app features.
///
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/auth_provider.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  static const List<Widget> _screens = [
    PropertyListScreen(), // Placeholder - need to create
    TenantListScreen(), // Placeholder - need to create
    BillListScreen(), // Placeholder - need to create
    PaymentListScreen(), // Placeholder - need to create
    SettingsScreen(), // Placeholder - need to create
  ];

  static const List<String> _titles = [
    'Properties',
    'Tenants',
    'Bills',
    'Payments',
    'Settings',
  ];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();

    return Scaffold(
      appBar: AppBar(
        title: Text(_titles[_selectedIndex]),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await authProvider.logout();
              if (mounted) {
                Navigator.of(context).pushReplacementNamed('/login');
              }
            },
          ),
        ],
      ),
      body: _screens[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Properties',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.people),
            label: 'Tenants',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.receipt),
            label: 'Bills',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.payment),
            label: 'Payments',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings),
            label: 'Settings',
          ),
        ],
        currentIndex: _selectedIndex,
        onTap: _onItemTapped,
      ),
    );
  }
}

// Placeholder screens - need to be implemented
class PropertyListScreen extends StatelessWidget {
  const PropertyListScreen({super.key});

  @override
  Widget build(BuildContext context) => const Center(
        child: Text('Properties Screen - Coming Soon'),
      );
}

class TenantListScreen extends StatelessWidget {
  const TenantListScreen({super.key});

  @override
  Widget build(BuildContext context) => const Center(
        child: Text('Tenants Screen - Coming Soon'),
      );
}

class BillListScreen extends StatelessWidget {
  const BillListScreen({super.key});

  @override
  Widget build(BuildContext context) => const Center(
        child: Text('Bills Screen - Coming Soon'),
      );
}

class PaymentListScreen extends StatelessWidget {
  const PaymentListScreen({super.key});

  @override
  Widget build(BuildContext context) => const Center(
        child: Text('Payments Screen - Coming Soon'),
      );
}

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) => const Center(
        child: Text('Settings Screen - Coming Soon'),
      );
}
