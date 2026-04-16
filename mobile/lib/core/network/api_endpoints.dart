class ApiEndpoints {
  ApiEndpoints._();

  // Auth
  static const String login = '/auth/login/';
  static const String register = '/auth/signup/';
  static const String logout = '/auth/logout/';
  static const String refresh = '/auth/refresh/';
  static const String me = '/users/me';
  static const String updateMe = '/users/me';
  static const String avatar = '/users/me/avatar';
  static const String changePassword = '/auth/change-password/';
  static const String passwordResetRequest = '/auth/password-reset-request/';
  static const String passwordResetConfirm = '/auth/password-reset-confirm/';
  static const String resendVerification = '/auth/resend-verification/';

  // Social Auth
  static const String socialProviders = '/auth/social/providers/';
  static String socialLogin(String provider) => '/auth/social/$provider/';

  // OTP / 2FA
  static const String otpEnable = '/auth/otp/enable/';
  static const String otpVerify = '/auth/otp/verify/';
  static const String otpValidate = '/auth/otp/validate/';
  static const String otpDisable = '/auth/otp/disable/';

  // Notifications
  static const String notifications = '/notifications/';
  static String markNotificationRead(String id) => '/notifications/$id/read/';
  static String deleteNotification(String id) => '/notifications/$id/';
  static const String markAllNotificationsRead = '/notifications/read-all/';
  static const String notificationPreferences = '/notifications/preferences/';
  static const String notificationDevices = '/notifications/devices/';
  static String notificationDevicesByProvider(String provider) =>
      '/notifications/devices/$provider/';
  static const String notificationPushConfig = '/notifications/push/config/';
  static const String systemCapabilities = '/system/capabilities/';
  static const String systemProviders = '/system/providers/';
  static const String systemGeneralSettings = '/system/general-settings/';

  // IAM - Token tracking
  static const String tokens = '/tokens/';
  static String revokeToken(String id) => '/tokens/revoke/$id';
  static const String revokeAll = '/tokens/revoke-all';

  // Payments
  static const String payments = '/payments/';
  static const String paymentProviders = '/payments/providers/';
  static const String paymentInitiate = '/payments/initiate/';
  static const String paymentVerify = '/payments/verify/';
  static const String invoices = '/invoices';
  static String invoiceById(String id) => '/invoices/$id';
  static String invoicePay(String id) => '/invoices/$id/pay';
  static String invoicePartialPay(String id) => '/invoices/$id/partial-pay';
  static String invoiceReceipt(String id) => '/invoices/$id/receipt';
  static String bookingRentLedger(String id) => '/bookings/$id/rent-ledger';
  static String additionalChargeDispute(String id) => '/additional-charges/$id/dispute';
  static const String tenantBillShares = '/tenants/me/bill-shares';
  static String billSharePay(String id) => '/bill-shares/$id/pay';
  static String billShareDispute(String id) => '/bill-shares/$id/dispute';
  static String utilityBillHistory(String id) => '/utility-bills/$id/history';

  // Listings
  static const String categories = '/categories';
  static String categoryById(String id) => '/categories/$id';
  static const String assets = '/assets';
  static String propertyById(String id) => '/properties/$id';
  static String propertyAvailability(String id) =>
      '/properties/$id/availability';
  static String propertyPrice(String id) => '/properties/$id/price';

  // Applications / bookings
  static const String bookings = '/bookings';
  static String bookingById(String id) => '/bookings/$id';
  static String bookingConfirm(String id) => '/bookings/$id/confirm';
  static String bookingDecline(String id) => '/bookings/$id/decline';
  static String bookingCancel(String id) => '/bookings/$id/cancel';
  static String bookingReturn(String id) => '/bookings/$id/return';
  static String bookingEvents(String id) => '/bookings/$id/events';
  static String bookingAgreement(String id) => '/bookings/$id/agreement';
  static String bookingAgreementSend(String id) =>
      '/bookings/$id/agreement/send';
  static String bookingAgreementCountersign(String id) =>
      '/bookings/$id/agreement/countersign';
}
