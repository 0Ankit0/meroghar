/// Home screen with bottom navigation and role-based views
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/constants.dart';
import '../providers/auth_provider.dart';
import '../providers/property_provider.dart';
import '../providers/tenant_provider.dart';
import '../providers/payment_provider.dart';
import 'properties/property_list_screen.dart';
import 'tenants/tenant_list_screen.dart';
import 'payments/payment_list_screen.dart';
import 'settings/profile_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  List<Widget> _getScreens(String userRole) {
    // Return different screens based on user role
    if (userRole == UserRoles.tenant) {
      return const [
        DashboardTab(),
        MyPaymentsTab(),
        MyBillsTab(),
        MyDocumentsTab(),
        SettingsTab(),
      ];
    } else {
      // Owner and Intermediary get full access
      return const [
        DashboardTab(),
        PropertiesTab(),
        TenantsTab(),
        PaymentsTab(),
        MoreTab(),
      ];
    }
  }

  List<BottomNavigationBarItem> _getNavItems(String userRole) {
    if (userRole == UserRoles.tenant) {
      return const [
        BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Dashboard'),
        BottomNavigationBarItem(icon: Icon(Icons.payment), label: 'Payments'),
        BottomNavigationBarItem(icon: Icon(Icons.receipt), label: 'Bills'),
        BottomNavigationBarItem(icon: Icon(Icons.folder), label: 'Documents'),
        BottomNavigationBarItem(icon: Icon(Icons.settings), label: 'Settings'),
      ];
    } else {
      return const [
        BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Dashboard'),
        BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Properties'),
        BottomNavigationBarItem(icon: Icon(Icons.people), label: 'Tenants'),
        BottomNavigationBarItem(icon: Icon(Icons.payment), label: 'Payments'),
        BottomNavigationBarItem(icon: Icon(Icons.more_horiz), label: 'More'),
      ];
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final userRole = authProvider.user?.role ?? UserRoles.tenant;
    final screens = _getScreens(userRole);
    final navItems = _getNavItems(userRole);

    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        items: navItems,
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        selectedItemColor: Theme.of(context).colorScheme.primary,
        unselectedItemColor: Colors.grey,
      ),
    );
  }
}

// Dashboard Tab
class DashboardTab extends StatelessWidget {
  const DashboardTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications),
            onPressed: () => Navigator.pushNamed(context, AppRoutes.notifications),
          ),
          IconButton(
            icon: const Icon(Icons.account_circle),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const ProfileScreen()),
              );
            },
            tooltip: 'Profile',
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(UIConstants.spacingM),
        children: [
          _buildWelcomeCard(context),
          const SizedBox(height: UIConstants.spacingM),
          _buildQuickStats(context),
          const SizedBox(height: UIConstants.spacingM),
          _buildQuickActions(context),
        ],
      ),
    );
  }

  Widget _buildWelcomeCard(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(UIConstants.spacingM),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Welcome back,', style: Theme.of(context).textTheme.bodyMedium),
            Text(
              authProvider.user?.name ?? 'User',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickStats(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: UIConstants.spacingS,
      crossAxisSpacing: UIConstants.spacingS,
      childAspectRatio: 1.5,
      children: [
        _buildStatCard(context, 'Properties', '0', Icons.home, Colors.blue),
        _buildStatCard(context, 'Tenants', '0', Icons.people, Colors.green),
        _buildStatCard(context, 'Payments', '0', Icons.payment, Colors.orange),
        _buildStatCard(context, 'Bills', '0', Icons.receipt, Colors.purple),
      ],
    );
  }

  Widget _buildStatCard(BuildContext context, String title, String value, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(UIConstants.spacingS),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: UIConstants.iconL, color: color),
            const SizedBox(height: UIConstants.spacingXs),
            Text(value, style: Theme.of(context).textTheme.headlineSmall),
            Text(title, style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickActions(BuildContext context) {
    return Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(UIConstants.spacingM),
            child: Text('Quick Actions', style: Theme.of(context).textTheme.titleMedium),
          ),
          ListTile(
            leading: const Icon(Icons.add_home),
            title: const Text('Add Property'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.pushNamed(context, AppRoutes.propertyCreate),
          ),
          ListTile(
            leading: const Icon(Icons.person_add),
            title: const Text('Add Tenant'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.pushNamed(context, AppRoutes.tenantCreate),
          ),
          ListTile(
            leading: const Icon(Icons.add_card),
            title: const Text('Record Payment'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.pushNamed(context, AppRoutes.paymentCreate),
          ),
          ListTile(
            leading: const Icon(Icons.build),
            title: const Text('Maintenance Request'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.pushNamed(context, AppRoutes.maintenance),
          ),
        ],
      ),
    );
  }
}

// Properties Tab
class PropertiesTab extends StatelessWidget {
  const PropertiesTab({super.key});

  @override
  Widget build(BuildContext context) {
    return const PropertyListScreen();
  }
}

// Tenants Tab
class TenantsTab extends StatelessWidget {
  const TenantsTab({super.key});

  @override
  Widget build(BuildContext context) {
    return const TenantListScreen();
  }
}

// Payments Tab
class PaymentsTab extends StatelessWidget {
  const PaymentsTab({super.key});

  @override
  Widget build(BuildContext context) {
    return const PaymentListScreen();
  }
}

// My Payments Tab (for tenants)
class MyPaymentsTab extends StatelessWidget {
  const MyPaymentsTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Payments')),
      body: const Center(child: Text('Your payment history will appear here')),
    );
  }
}

// My Bills Tab (for tenants)
class MyBillsTab extends StatelessWidget {
  const MyBillsTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Bills')),
      body: const Center(child: Text('Your bills will appear here')),
    );
  }
}

// My Documents Tab (for tenants)
class MyDocumentsTab extends StatelessWidget {
  const MyDocumentsTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Documents')),
      body: const Center(child: Text('Your documents will appear here')),
    );
  }
}

// More Tab
class MoreTab extends StatelessWidget {
  const MoreTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('More')),
      body: ListView(
        children: [
          ListTile(
            leading: const Icon(Icons.receipt),
            title: const Text('Bills'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showComingSoon(context),
          ),
          ListTile(
            leading: const Icon(Icons.build),
            title: const Text('Maintenance'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.pushNamed(context, AppRoutes.maintenance),
          ),
          ListTile(
            leading: const Icon(Icons.money_off),
            title: const Text('Expenses'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showComingSoon(context),
          ),
          ListTile(
            leading: const Icon(Icons.folder),
            title: const Text('Documents'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showComingSoon(context),
          ),
          ListTile(
            leading: const Icon(Icons.message),
            title: const Text('Messages'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showComingSoon(context),
          ),
          ListTile(
            leading: const Icon(Icons.analytics),
            title: const Text('Analytics'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showComingSoon(context),
          ),
          ListTile(
            leading: const Icon(Icons.assessment),
            title: const Text('Reports'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showComingSoon(context),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.settings),
            title: const Text('Settings'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.pushNamed(context, AppRoutes.settings),
          ),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Logout'),
            onTap: () async {
              final authProvider = context.read<AuthProvider>();
              await authProvider.logout();
              if (context.mounted) {
                Navigator.of(context).pushReplacementNamed(AppRoutes.login);
              }
            },
          ),
        ],
      ),
    );
  }

  void _showComingSoon(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Feature coming soon!')),
    );
  }
}

// Settings Tab
class SettingsTab extends StatelessWidget {
  const SettingsTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          ListTile(
            leading: const Icon(Icons.person),
            title: const Text('Profile'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.pushNamed(context, AppRoutes.settingsProfile),
          ),
          ListTile(
            leading: const Icon(Icons.notifications),
            title: const Text('Notifications'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.pushNamed(context, AppRoutes.settingsNotifications),
          ),
          ListTile(
            leading: const Icon(Icons.language),
            title: const Text('Language'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.pushNamed(context, AppRoutes.settingsLanguage),
          ),
          ListTile(
            leading: const Icon(Icons.dark_mode),
            title: const Text('Theme'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.pushNamed(context, AppRoutes.settingsTheme),
          ),
          ListTile(
            leading: const Icon(Icons.sync),
            title: const Text('Sync'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.pushNamed(context, AppRoutes.settingsSync),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.info),
            title: const Text('About'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.pushNamed(context, AppRoutes.settingsAbout),
          ),
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.red),
            title: const Text('Logout', style: TextStyle(color: Colors.red)),
            onTap: () async {
              final authProvider = context.read<AuthProvider>();
              await authProvider.logout();
              if (context.mounted) {
                Navigator.of(context).pushReplacementNamed(AppRoutes.login);
              }
            },
          ),
        ],
      ),
    );
  }
}
