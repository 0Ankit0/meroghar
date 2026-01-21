/// MeroGhar Rental Management Application
///
/// Main entry point with notification badge support and localization.
/// Implements T215, T250 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:flutter_app_badge/flutter_app_badge.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';

import 'config/app_router.dart';
import 'config/constants.dart';
import 'providers/analytics_provider.dart';
import 'providers/auth_provider.dart';
import 'providers/bill_provider.dart';
import 'providers/document_provider.dart';
import 'providers/expense_provider.dart';
import 'providers/language_provider.dart';
import 'providers/message_provider.dart';
import 'providers/maintenance_provider.dart';
import 'providers/notification_provider.dart';
import 'providers/payment_provider.dart';
import 'providers/property_provider.dart';
import 'providers/tenant_provider.dart';
import 'screens/auth/login_screen.dart';
import 'screens/home_screen.dart';
import 'services/api_service.dart';
import 'services/secure_storage_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize notification badge support
  await _initializeBadgeSupport();

  runApp(
    MultiProvider(
      providers: [
        Provider(create: (_) => ApiService()),
        Provider(create: (_) => SecureStorageService()),
        ChangeNotifierProvider(create: (_) => LanguageProvider()),
        ChangeNotifierProxyProvider2<ApiService, SecureStorageService,
            AuthProvider>(
          create: (context) => AuthProvider(
            apiService: context.read<ApiService>(),
            storageService: context.read<SecureStorageService>(),
          ),
          update: (context, apiService, storageService, previous) =>
              previous ??
              AuthProvider(
                apiService: apiService,
                storageService: storageService,
              ),
        ),
        ChangeNotifierProxyProvider<ApiService, PropertyProvider>(
          create: (context) => PropertyProvider(context.read<ApiService>()),
          update: (context, apiService, previous) =>
              previous ?? PropertyProvider(apiService),
        ),
        ChangeNotifierProxyProvider<ApiService, TenantProvider>(
          create: (context) => TenantProvider(context.read<ApiService>()),
          update: (context, apiService, previous) =>
              previous ?? TenantProvider(apiService),
        ),
        ChangeNotifierProxyProvider<ApiService, PaymentProvider>(
          create: (context) => PaymentProvider(context.read<ApiService>()),
          update: (context, apiService, previous) =>
              previous ?? PaymentProvider(apiService),
        ),
        ChangeNotifierProxyProvider<ApiService, BillProvider>(
          create: (context) => BillProvider(context.read<ApiService>()),
          update: (context, apiService, previous) =>
              previous ?? BillProvider(apiService),
        ),
        ChangeNotifierProxyProvider<ApiService, ExpenseProvider>(
          create: (context) => ExpenseProvider(context.read<ApiService>()),
          update: (context, apiService, previous) =>
              previous ?? ExpenseProvider(apiService),
        ),
        ChangeNotifierProxyProvider<ApiService, DocumentProvider>(
          create: (context) => DocumentProvider(context.read<ApiService>()),
          update: (context, apiService, previous) =>
              previous ?? DocumentProvider(apiService),
        ),
        ChangeNotifierProxyProvider<ApiService, MessageProvider>(
          create: (context) => MessageProvider(context.read<ApiService>()),
          update: (context, apiService, previous) =>
              previous ?? MessageProvider(apiService),
        ),
        ChangeNotifierProxyProvider<ApiService, NotificationProvider>(
          create: (context) => NotificationProvider(context.read<ApiService>()),
          update: (context, apiService, previous) =>
              previous ?? NotificationProvider(apiService),
        ),
        ChangeNotifierProxyProvider<ApiService, AnalyticsProvider>(
          create: (context) => AnalyticsProvider(context.read<ApiService>()),
          update: (context, apiService, previous) =>
              previous ?? AnalyticsProvider(apiService),
        ),
        ChangeNotifierProxyProvider<ApiService, MaintenanceProvider>(
          create: (context) => MaintenanceProvider(),  // MaintenanceProvider handles its own ApiService.instance
          update: (context, apiService, previous) => previous ?? MaintenanceProvider(),
        ),
      ],
      child: const MyApp(),
    ),
  );
}

/// Initialize notification badge support for the app.
Future<void> _initializeBadgeSupport() async {
  try {
    // Clear any existing badge on app start
    await FlutterAppBadge.count(0);
  } catch (e) {
    print('Error initializing badge support: $e');
  }
}

/// Update the app icon badge with unread notification count.
///
/// [count] - Number of unread notifications
Future<void> updateNotificationBadge(int count) async {
  try {
    await FlutterAppBadge.count(count);
  } catch (e) {
    print('Error updating notification badge: $e');
  }
}

/// Clear the app icon badge.
Future<void> clearNotificationBadge() async {
  try {
    await FlutterAppBadge.count(0);
  } catch (e) {
    print('Error clearing notification badge: $e');
  }
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) => Consumer<LanguageProvider>(
        builder: (context, languageProvider, child) => MaterialApp(
          title: 'MeroGhar',

          // Localization configuration
          locale: languageProvider.currentLocale,
          supportedLocales: LanguageProvider.supportedLocales,
          localizationsDelegates: const [
            // AppLocalizations.delegate, // Will be generated by flutter gen-l10n
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],

          // RTL support
          builder: (context, child) {
            // Force RTL for Arabic
            if (languageProvider.isRTL) {
              return Directionality(
                textDirection: TextDirection.rtl,
                child: child!,
              );
            }
            return child!;
          },

          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
            useMaterial3: true,
            cardTheme: CardTheme(
              elevation: 2,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(UIConstants.radiusM),
              ),
            ),
            inputDecorationTheme: InputDecorationTheme(
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(UIConstants.radiusM),
              ),
            ),
          ),

          // Routing
          initialRoute: '/',
          onGenerateRoute: AppRouter.generateRoute,
        ),
      );
}
