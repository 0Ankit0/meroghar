/// Application routing configuration
/// 
/// This file defines all routes and navigation logic for the app.
library;

import 'package:flutter/material.dart';

import '../config/constants.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/home_screen.dart';

class AppRouter {
  /// Generate routes based on route settings
  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      // Auth routes
      case AppRoutes.login:
        return MaterialPageRoute(builder: (_) => const LoginScreen());
      
      case AppRoutes.register:
        return MaterialPageRoute(builder: (_) => const RegisterScreen());
      
      case AppRoutes.forgotPassword:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Forgot Password'),
        );
      
      case AppRoutes.resetPassword:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Reset Password'),
        );

      // Main routes
      case AppRoutes.home:
      case AppRoutes.dashboard:
        return MaterialPageRoute(builder: (_) => const HomeScreen());

      // Property routes
      case AppRoutes.properties:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Properties'),
        );
      
      case AppRoutes.propertyCreate:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Add Property'),
        );

      // Tenant routes
      case AppRoutes.tenants:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Tenants'),
        );
      
      case AppRoutes.tenantCreate:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Add Tenant'),
        );

      // Payment routes
      case AppRoutes.payments:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Payments'),
        );
      
      case AppRoutes.paymentCreate:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Record Payment'),
        );

      // Bill routes
      case AppRoutes.bills:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Bills'),
        );
      
      case AppRoutes.billCreate:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Add Bill'),
        );

      // Expense routes
      case AppRoutes.expenses:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Expenses'),
        );
      
      case AppRoutes.expenseCreate:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Add Expense'),
        );

      // Document routes
      case AppRoutes.documents:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Documents'),
        );
      
      case AppRoutes.documentUpload:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Upload Document'),
        );

      // Message routes
      case AppRoutes.messages:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Messages'),
        );
      
      case AppRoutes.messageCompose:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Compose Message'),
        );
      
      case AppRoutes.messageBulk:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Bulk Messages'),
        );

      // Notification routes
      case AppRoutes.notifications:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Notifications'),
        );

      // Report routes
      case AppRoutes.reports:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Reports'),
        );
      
      case AppRoutes.reportGenerate:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Generate Report'),
        );

      // Analytics routes
      case AppRoutes.analytics:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Analytics'),
        );

      // Settings routes
      case AppRoutes.settings:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Settings'),
        );
      
      case AppRoutes.settingsProfile:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Profile Settings'),
        );
      
      case AppRoutes.settingsNotifications:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Notification Settings'),
        );
      
      case AppRoutes.settingsLanguage:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Language Settings'),
        );
      
      case AppRoutes.settingsTheme:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Theme Settings'),
        );
      
      case AppRoutes.settingsSync:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'Sync Settings'),
        );
      
      case AppRoutes.settingsAbout:
        return MaterialPageRoute(
          builder: (_) => const PlaceholderScreen(title: 'About'),
        );

      // Default - 404
      default:
        return MaterialPageRoute(
          builder: (_) => Scaffold(
            appBar: AppBar(title: const Text('Page Not Found')),
            body: const Center(
              child: Text('404 - Page not found'),
            ),
          ),
        );
    }
  }

  /// Navigate to a named route
  static Future<T?> navigateTo<T>(
    BuildContext context,
    String routeName, {
    Object? arguments,
  }) {
    return Navigator.pushNamed<T>(
      context,
      routeName,
      arguments: arguments,
    );
  }

  /// Navigate to a named route and remove all previous routes
  static Future<T?> navigateAndRemoveUntil<T>(
    BuildContext context,
    String routeName, {
    Object? arguments,
  }) {
    return Navigator.pushNamedAndRemoveUntil<T>(
      context,
      routeName,
      (route) => false,
      arguments: arguments,
    );
  }

  /// Replace current route with a new one
  static Future<T?> navigateReplace<T>(
    BuildContext context,
    String routeName, {
    Object? arguments,
  }) {
    return Navigator.pushReplacementNamed<T, T>(
      context,
      routeName,
      arguments: arguments,
    );
  }

  /// Go back to previous route
  static void goBack(BuildContext context, [Object? result]) {
    Navigator.pop(context, result);
  }

  /// Check if can go back
  static bool canGoBack(BuildContext context) {
    return Navigator.canPop(context);
  }
}

/// Placeholder screen for unimplemented features
class PlaceholderScreen extends StatelessWidget {
  const PlaceholderScreen({
    required this.title,
    super.key,
  });

  final String title;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.construction,
              size: 80,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 24),
            Text(
              '$title Screen',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              'Coming Soon',
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: Colors.grey[600],
                  ),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => Navigator.pop(context),
              icon: const Icon(Icons.arrow_back),
              label: const Text('Go Back'),
            ),
          ],
        ),
      ),
    );
  }
}
