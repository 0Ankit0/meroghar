import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../applications/application_access.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../listings/listing_access.dart';
import '../../../notifications/presentation/providers/notification_provider.dart';
import '../../../payments/payment_access.dart';

class HomeTab extends ConsumerWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final roles = ref.watch(authNotifierProvider).valueOrNull?.user?.roles ??
        const <String>[];
    final showManageListings = canManageListings(roles);
    final showApplications = canViewApplications(roles);
    final showBilling = canViewTenantBilling(roles);

    return Scaffold(
      appBar: AppBar(title: const Text('Home')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            'Quick Access',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          _QuickAccessCard(
            icon: Icons.travel_explore_outlined,
            title: 'Search Listings',
            subtitle: 'Browse homes, check availability, and preview quotes',
            color: Colors.deepPurple,
            onTap: () => context.go(AppConstants.listingsRoute),
          ),
          if (showApplications) ...[
            const SizedBox(height: 8),
            _QuickAccessCard(
              icon: Icons.assignment_outlined,
              title: 'My Applications',
              subtitle: 'Track approvals, lease signing, and move-out updates',
              color: Colors.blue,
              onTap: () => context.go(AppConstants.applicationsRoute),
            ),
          ],
          if (showBilling) ...[
            const SizedBox(height: 8),
            _QuickAccessCard(
              icon: Icons.receipt_long_outlined,
              title: 'Billing',
              subtitle: 'Rent invoices, utility shares, receipts, and history',
              color: Colors.indigo,
              onTap: () => context.go(AppConstants.paymentsRoute),
            ),
          ],
          const SizedBox(height: 8),
          _QuickAccessCard(
            icon: Icons.devices,
            title: 'Active Sessions',
            subtitle: 'View and revoke active tokens',
            color: Colors.teal,
            onTap: () => context.go(AppConstants.tokensRoute),
          ),
          if (showManageListings) ...[
            const SizedBox(height: 8),
            _QuickAccessCard(
              icon: Icons.add_home_work_outlined,
              title: 'Create Draft Listing',
              subtitle:
                  'Start a landlord draft with category and pricing basics',
              color: Colors.orange,
              onTap: () => context.go(AppConstants.manageListingsRoute),
            ),
          ],
        ],
      ),
    );
  }
}

class _QuickAccessCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  const _QuickAccessCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withValues(alpha: 0.12),
          child: Icon(icon, color: color),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w500)),
        subtitle: Text(subtitle,
            style: const TextStyle(fontSize: 12, color: Colors.grey)),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}

class HomePage extends ConsumerWidget {
  final StatefulNavigationShell navigationShell;

  const HomePage({super.key, required this.navigationShell});

  static const _destinations = [
    NavigationDestination(
        icon: Icon(Icons.home_outlined),
        selectedIcon: Icon(Icons.home),
        label: 'Home'),
    NavigationDestination(
        icon: Icon(Icons.notifications_outlined),
        selectedIcon: Icon(Icons.notifications),
        label: 'Notifications'),
    NavigationDestination(
        icon: Icon(Icons.settings_outlined),
        selectedIcon: Icon(Icons.settings),
        label: 'Settings'),
    NavigationDestination(
        icon: Icon(Icons.person_outline),
        selectedIcon: Icon(Icons.person),
        label: 'Profile'),
  ];

  void _onDestinationSelected(int index) {
    navigationShell.goBranch(
      index,
      initialLocation: index == navigationShell.currentIndex,
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final unreadAsync = ref.watch(unreadCountProvider);
    final unreadCount = unreadAsync.valueOrNull ?? 0;

    final destinations = [
      _destinations[0],
      NavigationDestination(
        icon: Badge(
          isLabelVisible: unreadCount > 0,
          label: Text(unreadCount > 99 ? '99+' : '$unreadCount'),
          child: const Icon(Icons.notifications_outlined),
        ),
        selectedIcon: Badge(
          isLabelVisible: unreadCount > 0,
          label: Text(unreadCount > 99 ? '99+' : '$unreadCount'),
          child: const Icon(Icons.notifications),
        ),
        label: 'Notifications',
      ),
      _destinations[2],
      _destinations[3],
    ];

    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: navigationShell.currentIndex,
        onDestinationSelected: _onDestinationSelected,
        destinations: destinations,
      ),
    );
  }
}
