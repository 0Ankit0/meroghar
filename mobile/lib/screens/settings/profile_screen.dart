/// User profile screen showing account details and settings.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../config/constants.dart';
import '../../providers/auth_provider.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final user = authProvider.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () {
              // Navigate to edit profile
              Navigator.pushNamed(context, AppRoutes.settingsProfile);
            },
            tooltip: 'Edit Profile',
          ),
        ],
      ),
      body: user == null
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(UIConstants.spacingM),
              children: [
                // Profile Header
                Center(
                  child: Column(
                    children: [
                      CircleAvatar(
                        radius: 60,
                        backgroundColor: Theme.of(context).primaryColor,
                        child: Text(
                          user.fullName[0].toUpperCase(),
                          style: const TextStyle(
                            fontSize: 48,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(height: UIConstants.spacingM),
                      Text(
                        user.fullName,
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                      const SizedBox(height: UIConstants.spacingXs),
                      Text(
                        user.email,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Colors.grey[600],
                            ),
                      ),
                      const SizedBox(height: UIConstants.spacingXs),
                      Chip(
                        label: Text(user.role.value.toUpperCase()),
                        backgroundColor: Theme.of(context).primaryColor.withOpacity(0.1),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: UIConstants.spacingL),
                
                // Account Information
                Card(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(UIConstants.spacingM),
                        child: Text(
                          'Account Information',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ),
                      _buildInfoTile(
                        context,
                        Icons.email,
                        'Email',
                        user.email,
                      ),
                      if (user.phone != null)
                        _buildInfoTile(
                          context,
                          Icons.phone,
                          'Phone',
                          user.phone!,
                        ),
                      _buildInfoTile(
                        context,
                        Icons.badge,
                        'Role',
                        user.role.value.toUpperCase(),
                      ),
                      _buildInfoTile(
                        context,
                        Icons.verified,
                        'Status',
                        user.isActive ? 'Active' : 'Inactive',
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: UIConstants.spacingM),
                
                // Settings & Actions
                Card(
                  child: Column(
                    children: [
                      ListTile(
                        leading: const Icon(Icons.person),
                        title: const Text('Edit Profile'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () {
                          Navigator.pushNamed(context, AppRoutes.settingsProfile);
                        },
                      ),
                      ListTile(
                        leading: const Icon(Icons.lock),
                        title: const Text('Change Password'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () {
                          // TODO: Navigate to change password
                        },
                      ),
                      ListTile(
                        leading: const Icon(Icons.notifications),
                        title: const Text('Notification Settings'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () {
                          Navigator.pushNamed(context, AppRoutes.settingsNotifications);
                        },
                      ),
                      ListTile(
                        leading: const Icon(Icons.language),
                        title: const Text('Language'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () {
                          Navigator.pushNamed(context, AppRoutes.settingsLanguage);
                        },
                      ),
                      const Divider(),
                      ListTile(
                        leading: const Icon(Icons.logout, color: Colors.red),
                        title: const Text(
                          'Logout',
                          style: TextStyle(color: Colors.red),
                        ),
                        onTap: () async {
                          final confirmed = await _showLogoutConfirmation(context);
                          if (confirmed == true && context.mounted) {
                            await authProvider.logout();
                            if (context.mounted) {
                              Navigator.of(context)
                                  .pushReplacementNamed(AppRoutes.login);
                            }
                          }
                        },
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildInfoTile(
    BuildContext context,
    IconData icon,
    String label,
    String value,
  ) {
    return ListTile(
      leading: Icon(icon, color: Colors.grey[600]),
      title: Text(label),
      subtitle: Text(value),
    );
  }

  Future<bool?> _showLogoutConfirmation(BuildContext context) {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Logout'),
        content: const Text('Are you sure you want to logout?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Logout'),
          ),
        ],
      ),
    );
  }
}
