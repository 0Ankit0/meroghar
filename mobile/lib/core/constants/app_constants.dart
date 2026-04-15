class AppConstants {
  AppConstants._();

  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';

  // Route names
  static const String loginRoute = '/login';
  static const String registerRoute = '/register';
  static const String forgotPasswordRoute = '/forgot-password';
  static const String otpVerifyRoute = '/otp-verify';
  static const String resetPasswordRoute = '/reset-password';
  static const String homeRoute = '/home';
  static const String notificationsRoute = '/home/notifications';
  static const String settingsRoute = '/home/settings';
  static const String profileRoute = '/home/profile';
  static const String tokensRoute = '/home/settings/tokens';
  static const String paymentsRoute = '/home/payments';
  static const String listingsRoute = '/home/listings';
  static const String manageListingsRoute = '/home/listings/manage';
  static const String applicationsRoute = '/home/applications';

  static String listingDetailRoute(String listingId) =>
      '$listingsRoute/$listingId';
  static String applicationDetailRoute(String bookingId) =>
      '$applicationsRoute/$bookingId';
  static String applicationLeaseRoute(String bookingId) =>
      '${applicationDetailRoute(bookingId)}/lease';

  // Social auth — the backend redirects here after OAuth; the WebView intercepts it
  static const String socialAuthCallbackPrefix = '/auth-callback';
}
