/// Application-wide constants for Meroghar Mobile App
/// 
/// This file contains all constants used throughout the application
/// for easy maintenance and configuration management.
library;

/// API Endpoints
class ApiEndpoints {
  // Base paths
  static const String auth = '/auth';
  static const String users = '/users';
  static const String properties = '/properties';
  static const String tenants = '/tenants';
  static const String payments = '/payments';
  static const String bills = '/bills';
  static const String expenses = '/expenses';
  static const String documents = '/documents';
  static const String messages = '/messages';
  static const String notifications = '/notifications';
  static const String reports = '/reports';
  static const String analytics = '/analytics';
  static const String sync = '/sync';

  // Auth endpoints
  static const String login = '$auth/login';
  static const String register = '$auth/register';
  static const String logout = '$auth/logout';
  static const String refresh = '$auth/refresh';
  static const String forgotPassword = '$auth/forgot-password';
  static const String resetPassword = '$auth/reset-password';
  static const String changePassword = '$auth/change-password';
  static const String verifyEmail = '$auth/verify-email';

  // User endpoints
  static const String userProfile = '$users/me';
  static const String updateProfile = '$users/me';
  static const String userList = users;

  // Property endpoints
  static const String propertyList = properties;
  static const String propertyCreate = properties;
  static String propertyDetail(String id) => '$properties/$id';
  static String propertyUpdate(String id) => '$properties/$id';
  static String propertyDelete(String id) => '$properties/$id';
  static String propertyTenants(String id) => '$properties/$id/tenants';
  static String propertyBills(String id) => '$properties/$id/bills';

  // Tenant endpoints
  static const String tenantList = tenants;
  static const String tenantCreate = tenants;
  static String tenantDetail(String id) => '$tenants/$id';
  static String tenantUpdate(String id) => '$tenants/$id';
  static String tenantDelete(String id) => '$tenants/$id';
  static String tenantPayments(String id) => '$tenants/$id/payments';
  static String tenantBills(String id) => '$tenants/$id/bills';

  // Payment endpoints
  static const String paymentList = payments;
  static const String paymentCreate = payments;
  static String paymentDetail(String id) => '$payments/$id';
  static String paymentReceipt(String id) => '$payments/$id/receipt';
  static const String paymentGatewayInitiate = '$payments/gateway/initiate';
  static const String paymentGatewayVerify = '$payments/gateway/verify';

  // Bill endpoints
  static const String billList = bills;
  static const String billCreate = bills;
  static String billDetail(String id) => '$bills/$id';
  static String billUpdate(String id) => '$bills/$id';
  static String billAllocate(String id) => '$bills/$id/allocate';
  static String billPayments(String id) => '$bills/$id/payments';

  // Expense endpoints
  static const String expenseList = expenses;
  static const String expenseCreate = expenses;
  static String expenseDetail(String id) => '$expenses/$id';
  static String expenseUpdate(String id) => '$expenses/$id';
  static String expenseApprove(String id) => '$expenses/$id/approve';

  // Maintenance endpoints
  static const String maintenance = '/maintenance';
  static String maintenanceDetail(String id) => '$maintenance/$id';

  // Document endpoints
  static const String documentList = documents;
  static const String documentUpload = documents;
  static String documentDownload(String id) => '$documents/$id/download';
  static String documentDelete(String id) => '$documents/$id';

  // Message endpoints
  static const String messageList = messages;
  static const String messageSend = messages;
  static const String messageBulkSend = '$messages/bulk';
  static const String messageTemplates = '$messages/templates';

  // Notification endpoints
  static const String notificationList = notifications;
  static String notificationRead(String id) => '$notifications/$id/read';
  static const String notificationReadAll = '$notifications/read-all';
  static const String notificationSettings = '$notifications/settings';

  // Report endpoints
  static const String reportGenerate = '$reports/generate';
  static const String reportExport = '$reports/export';
  static const String reportTax = '$reports/tax';

  // Analytics endpoints
  static const String analyticsDashboard = '$analytics/dashboard';
  static const String analyticsRevenue = '$analytics/revenue';
  static const String analyticsExpenses = '$analytics/expenses';
  static const String analyticsOccupancy = '$analytics/occupancy';

  // Sync endpoints
  static const String syncUp = '$sync/up';
  static const String syncDown = '$sync/down';
  static const String syncStatus = '$sync/status';
  static const String syncConflicts = '$sync/conflicts';
}

/// App Routes
class AppRoutes {
  // Auth routes
  static const String login = '/login';
  static const String register = '/register';
  static const String forgotPassword = '/forgot-password';
  static const String resetPassword = '/reset-password';

  // Main routes
  static const String home = '/home';
  static const String dashboard = '/dashboard';

  // Property routes
  static const String properties = '/properties';
  static const String propertyDetail = '/properties/:id';
  static const String propertyCreate = '/properties/create';
  static const String propertyEdit = '/properties/:id/edit';

  // Tenant routes
  static const String tenants = '/tenants';
  static const String tenantDetail = '/tenants/:id';
  static const String tenantCreate = '/tenants/create';
  static const String tenantRecordCreate = '/tenants/record-create';
  static const String tenantEdit = '/tenants/:id/edit';

  // Payment routes
  static const String payments = '/payments';
  static const String paymentDetail = '/payments/:id';
  static const String paymentCreate = '/payments/create';
  static const String paymentReceipt = '/payments/:id/receipt';

  // Bill routes
  static const String bills = '/bills';
  static const String billDetail = '/bills/:id';
  static const String billCreate = '/bills/create';
  static const String billAllocate = '/bills/:id/allocate';

  // Expense routes
  static const String expenses = '/expenses';
  static const String expenseDetail = '/expenses/:id';
  static const String expenseCreate = '/expenses/create';

  // Maintenance routes
  static const String maintenance = '/maintenance';
  static const String maintenanceCreate = '/maintenance/create';
  static const String maintenanceDetail = '/maintenance/:id';

  // Document routes
  static const String documents = '/documents';
  static const String documentView = '/documents/:id';
  static const String documentUpload = '/documents/upload';

  // Message routes
  static const String messages = '/messages';
  static const String messageCompose = '/messages/compose';
  static const String messageBulk = '/messages/bulk';

  // Notification routes
  static const String notifications = '/notifications';

  // Report routes
  static const String reports = '/reports';
  static const String reportGenerate = '/reports/generate';
  static const String reportTax = '/reports/tax';

  // Analytics routes
  static const String analytics = '/analytics';

  // Settings routes
  static const String settings = '/settings';
  static const String settingsProfile = '/settings/profile';
  static const String settingsNotifications = '/settings/notifications';
  static const String settingsLanguage = '/settings/language';
  static const String settingsTheme = '/settings/theme';
  static const String settingsSync = '/settings/sync';
  static const String settingsAbout = '/settings/about';
}

/// User Roles
class UserRoles {
  static const String owner = 'OWNER';
  static const String intermediary = 'INTERMEDIARY';
  static const String tenant = 'TENANT';
}

/// Payment Methods
class PaymentMethods {
  static const String cash = 'CASH';
  static const String bankTransfer = 'BANK_TRANSFER';
  static const String upi = 'UPI';
  static const String card = 'CARD';
  static const String khalti = 'KHALTI';
  static const String esewa = 'ESEWA';
  static const String imepay = 'IMEPAY';
  static const String online = 'ONLINE';
}

/// Payment Status
class PaymentStatus {
  static const String pending = 'PENDING';
  static const String completed = 'COMPLETED';
  static const String failed = 'FAILED';
  static const String refunded = 'REFUNDED';
}

/// Bill Types
class BillTypes {
  static const String electricity = 'ELECTRICITY';
  static const String water = 'WATER';
  static const String gas = 'GAS';
  static const String internet = 'INTERNET';
  static const String maintenance = 'MAINTENANCE';
  static const String other = 'OTHER';
}

/// Expense Categories
class ExpenseCategories {
  static const String maintenance = 'MAINTENANCE';
  static const String repair = 'REPAIR';
  static const String cleaning = 'CLEANING';
  static const String utilities = 'UTILITIES';
  static const String tax = 'TAX';
  static const String insurance = 'INSURANCE';
  static const String other = 'OTHER';
}

/// Document Types
class DocumentTypes {
  static const String lease = 'LEASE';
  static const String idProof = 'ID_PROOF';
  static const String addressProof = 'ADDRESS_PROOF';
  static const String noc = 'NOC';
  static const String receipt = 'RECEIPT';
  static const String other = 'OTHER';
}

/// Notification Types
class NotificationTypes {
  static const String payment = 'PAYMENT';
  static const String bill = 'BILL';
  static const String message = 'MESSAGE';
  static const String reminder = 'REMINDER';
  static const String announcement = 'ANNOUNCEMENT';
  static const String alert = 'ALERT';
}

/// Sync Status
class SyncStatus {
  static const String synced = 'SYNCED';
  static const String pending = 'PENDING';
  static const String failed = 'FAILED';
  static const String conflict = 'CONFLICT';
}

/// Report Types
class ReportTypes {
  static const String payment = 'PAYMENT';
  static const String expense = 'EXPENSE';
  static const String income = 'INCOME';
  static const String tax = 'TAX';
  static const String occupancy = 'OCCUPANCY';
}

/// Export Formats
class ExportFormats {
  static const String pdf = 'PDF';
  static const String excel = 'EXCEL';
  static const String csv = 'CSV';
}

/// Date Formats
class DateFormats {
  static const String display = 'dd/MM/yyyy';
  static const String displayWithTime = 'dd/MM/yyyy HH:mm';
  static const String api = 'yyyy-MM-dd';
  static const String apiWithTime = "yyyy-MM-dd'T'HH:mm:ss'Z'";
}

/// Validation Constants
class ValidationConstants {
  // Text field lengths
  static const int nameMinLength = 2;
  static const int nameMaxLength = 100;
  static const int emailMaxLength = 255;
  static const int phoneMinLength = 10;
  static const int phoneMaxLength = 15;
  static const int passwordMinLength = 8;
  static const int passwordMaxLength = 128;
  static const int descriptionMaxLength = 500;

  // File sizes (in bytes)
  static const int maxImageSize = 10 * 1024 * 1024; // 10 MB
  static const int maxDocumentSize = 20 * 1024 * 1024; // 20 MB

  // Numeric limits
  static const double minAmount = 0.01;
  static const double maxAmount = 10000000.0;
}

/// Storage Keys
class StorageKeys {
  static const String accessToken = 'access_token';
  static const String refreshToken = 'refresh_token';
  static const String userId = 'user_id';
  static const String userRole = 'user_role';
  static const String userEmail = 'user_email';
  static const String userName = 'user_name';
  static const String selectedPropertyId = 'selected_property_id';
  static const String language = 'language';
  static const String theme = 'theme';
  static const String lastSyncTime = 'last_sync_time';
}

/// Database Tables
class DbTables {
  static const String properties = 'properties';
  static const String tenants = 'tenants';
  static const String payments = 'payments';
  static const String bills = 'bills';
  static const String billAllocations = 'bill_allocations';
  static const String expenses = 'expenses';
  static const String documents = 'documents';
  static const String messages = 'messages';
  static const String notifications = 'notifications';
  static const String syncQueue = 'sync_queue';
}

/// UI Constants
class UIConstants {
  // Spacing
  static const double spacingXs = 4.0;
  static const double spacingS = 8.0;
  static const double spacingM = 16.0;
  static const double spacingL = 24.0;
  static const double spacingXl = 32.0;

  // Border radius
  static const double radiusS = 4.0;
  static const double radiusM = 8.0;
  static const double radiusL = 12.0;
  static const double radiusXl = 16.0;

  // Icon sizes
  static const double iconS = 16.0;
  static const double iconM = 24.0;
  static const double iconL = 32.0;
  static const double iconXl = 48.0;

  // Animation durations
  static const Duration animationFast = Duration(milliseconds: 200);
  static const Duration animationNormal = Duration(milliseconds: 300);
  static const Duration animationSlow = Duration(milliseconds: 500);

  // List pagination
  static const int pageSize = 20;
  static const int maxPageSize = 100;
}

/// Error Messages
class ErrorMessages {
  static const String networkError = 'No internet connection. Please check your network.';
  static const String serverError = 'Server error. Please try again later.';
  static const String unauthorized = 'Session expired. Please login again.';
  static const String validationError = 'Please check your input and try again.';
  static const String notFound = 'Requested resource not found.';
  static const String unknownError = 'An unexpected error occurred.';
}

/// Success Messages
class SuccessMessages {
  static const String loginSuccess = 'Login successful';
  static const String logoutSuccess = 'Logout successful';
  static const String saveSuccess = 'Saved successfully';
  static const String deleteSuccess = 'Deleted successfully';
  static const String updateSuccess = 'Updated successfully';
  static const String paymentSuccess = 'Payment completed successfully';
  static const String syncSuccess = 'Sync completed successfully';
}

/// Regex Patterns
class RegexPatterns {
  static final RegExp email = RegExp(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
  );
  static final RegExp phone = RegExp(r'^\+?[\d\s-]{10,15}$');
  static final RegExp number = RegExp(r'^\d+$');
  static final RegExp decimal = RegExp(r'^\d+\.?\d{0,2}$');
}

/// Supported Languages
class SupportedLanguages {
  static const List<Map<String, String>> languages = [
    {'code': 'en', 'name': 'English', 'nativeName': 'English'},
    {'code': 'hi', 'name': 'Hindi', 'nativeName': 'हिन्दी'},
    {'code': 'ne', 'name': 'Nepali', 'nativeName': 'नेपाली'},
    {'code': 'es', 'name': 'Spanish', 'nativeName': 'Español'},
  ];
}

/// Supported Currencies
class SupportedCurrencies {
  static const List<Map<String, String>> currencies = [
    {'code': 'INR', 'symbol': '₹', 'name': 'Indian Rupee'},
    {'code': 'NPR', 'symbol': 'रू', 'name': 'Nepalese Rupee'},
    {'code': 'USD', 'symbol': '\$', 'name': 'US Dollar'},
    {'code': 'EUR', 'symbol': '€', 'name': 'Euro'},
  ];
}
