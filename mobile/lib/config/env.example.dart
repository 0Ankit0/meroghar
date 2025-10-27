/// Environment configuration for Meroghar Mobile App
///
/// Copy this file to `env.dart` and update with your actual configuration values.
/// The `env.dart` file is gitignored and should never be committed.
class Environment {
  // Application
  static const String appName = 'Meroghar';
  static const String appVersion = '0.1.0';

  // API Configuration
  static const String apiBaseUrl = 'http://localhost:8000/api/v1';
  static const String apiTimeout = '30'; // seconds

  // Environment Type
  static const String environment =
      'development'; // development, staging, production
  static const bool debugMode = true;

  // Storage
  static const String localDbName = 'meroghar.db';
  static const int localDbVersion = 1;

  // Security
  static const String secureStoragePrefix = 'meroghar_';
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userIdKey = 'user_id';

  // Push Notifications
  static const String fcmServerKey = 'your_fcm_server_key_here';
  static const String fcmSenderId = 'your_fcm_sender_id_here';

  // Firebase Configuration (Android)
  static const String firebaseAndroidApiKey = 'your_android_api_key';
  static const String firebaseAndroidAppId = 'your_android_app_id';
  static const String firebaseAndroidMessagingSenderId = 'your_sender_id';
  static const String firebaseAndroidProjectId = 'your_project_id';

  // Firebase Configuration (iOS)
  static const String firebaseIosApiKey = 'your_ios_api_key';
  static const String firebaseIosAppId = 'your_ios_app_id';
  static const String firebaseIosMessagingSenderId = 'your_sender_id';
  static const String firebaseIosProjectId = 'your_project_id';
  static const String firebaseIosBundleId = 'com.meroghar.mobile';

  // Payment Gateways
  static const String stripePublishableKey =
      'pk_test_your_stripe_publishable_key';
  static const String razorpayKeyId = 'your_razorpay_key_id';

  // Features Flags
  static const bool enableOfflineMode = true;
  static const bool enablePushNotifications = true;
  static const bool enableAnalytics = true;
  static const bool enableCrashReporting = true;

  // Sync Configuration
  static const int syncIntervalMinutes = 15;
  static const int maxRetryAttempts = 3;
  static const int retryDelaySeconds = 5;

  // File Upload
  static const int maxImageSizeMB = 10;
  static const int maxDocumentSizeMB = 20;
  static const List<String> allowedImageFormats = [
    'jpg',
    'jpeg',
    'png',
    'webp'
  ];
  static const List<String> allowedDocumentFormats = [
    'pdf',
    'jpg',
    'jpeg',
    'png'
  ];

  // Pagination
  static const int defaultPageSize = 20;
  static const int maxPageSize = 100;

  // Cache
  static const int cacheExpiryHours = 24;
  static const int imageCacheMaxSizeMB = 100;

  // Localization
  static const String defaultLocale = 'en';
  static const List<String> supportedLocales = ['en', 'hi', 'es'];

  // Currency
  static const String defaultCurrency = 'INR';
  static const String currencySymbol = '₹';

  // Date & Time
  static const String dateFormat = 'dd/MM/yyyy';
  static const String timeFormat = 'HH:mm';
  static const String dateTimeFormat = 'dd/MM/yyyy HH:mm';

  // Logging
  static const bool enableDebugLogs = true;
  static const bool enableNetworkLogs = true;
  static const bool apiLogRequests = true; // Log API requests/responses
  static const String logLevel = 'debug'; // debug, info, warning, error

  // Performance
  static const int startupTimeoutSeconds = 5;
  static const int syncTimeoutSeconds = 30;
  static const int apiRequestTimeoutSeconds = 30;

  // Deep Linking
  static const String deepLinkScheme = 'meroghar';
  static const String deepLinkHost = 'app.meroghar.com';

  // Support
  static const String supportEmail = 'support@meroghar.com';
  static const String supportPhone = '+91-1234567890';
  static const String privacyPolicyUrl = 'https://meroghar.com/privacy';
  static const String termsOfServiceUrl = 'https://meroghar.com/terms';

  // Development Tools
  static const bool showPerformanceOverlay = false;
  static const bool showSemanticsDebugger = false;
  static const bool debugShowCheckedModeBanner = false;
}
