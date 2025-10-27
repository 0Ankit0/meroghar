import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Provider for managing app language/locale state
///
/// Implements T216 from tasks.md.
///
/// Supports:
/// - English (en)
/// - Hindi (hi)
/// - Spanish (es)
/// - Arabic (ar) - with RTL support
///
/// Language preference is persisted using SharedPreferences.
class LanguageProvider with ChangeNotifier {
  static const String _languageKey = 'app_language';
  static const String _defaultLanguage = 'en';

  Locale _currentLocale = const Locale(_defaultLanguage);
  bool _isInitialized = false;

  /// Supported locales for the app
  static const List<Locale> supportedLocales = [
    Locale('en'), // English
    Locale('hi'), // Hindi
    Locale('es'), // Spanish
    Locale('ar'), // Arabic (RTL)
  ];

  /// Map of locale codes to display names
  static const Map<String, String> languageNames = {
    'en': 'English',
    'hi': 'हिंदी (Hindi)',
    'es': 'Español (Spanish)',
    'ar': 'العربية (Arabic)',
  };

  /// Map of locale codes to native names (for language picker)
  static const Map<String, String> nativeLanguageNames = {
    'en': 'English',
    'hi': 'हिंदी',
    'es': 'Español',
    'ar': 'العربية',
  };

  LanguageProvider() {
    _loadSavedLanguage();
  }

  /// Get current locale
  Locale get currentLocale => _currentLocale;

  /// Get current language code
  String get currentLanguageCode => _currentLocale.languageCode;

  /// Check if provider is initialized
  bool get isInitialized => _isInitialized;

  /// Check if current locale is RTL
  bool get isRTL => _currentLocale.languageCode == 'ar';

  /// Get display name for current language
  String get currentLanguageName =>
      languageNames[_currentLocale.languageCode] ?? 'English';

  /// Load saved language preference from SharedPreferences
  Future<void> _loadSavedLanguage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final savedLanguage = prefs.getString(_languageKey);

      if (savedLanguage != null) {
        final locale = Locale(savedLanguage);
        // Verify it's a supported locale
        if (supportedLocales.any((l) => l.languageCode == savedLanguage)) {
          _currentLocale = locale;
        }
      }

      _isInitialized = true;
      notifyListeners();
    } catch (e) {
      debugPrint('Error loading saved language: $e');
      _isInitialized = true;
      notifyListeners();
    }
  }

  /// Change app language
  ///
  /// [languageCode] - ISO 639-1 language code (e.g., 'en', 'hi', 'es', 'ar')
  ///
  /// Returns true if language was changed successfully
  Future<bool> changeLanguage(String languageCode) async {
    try {
      // Validate language code
      if (!supportedLocales.any((l) => l.languageCode == languageCode)) {
        debugPrint('Unsupported language code: $languageCode');
        return false;
      }

      // Don't change if already current
      if (_currentLocale.languageCode == languageCode) {
        return true;
      }

      final newLocale = Locale(languageCode);

      // Save to SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_languageKey, languageCode);

      // Update state
      _currentLocale = newLocale;
      notifyListeners();

      return true;
    } catch (e) {
      debugPrint('Error changing language: $e');
      return false;
    }
  }

  /// Reset to default language (English)
  Future<void> resetToDefault() async {
    await changeLanguage(_defaultLanguage);
  }

  /// Get list of all supported languages with their display names
  List<LanguageOption> getSupportedLanguages() {
    return supportedLocales.map((locale) {
      return LanguageOption(
        code: locale.languageCode,
        name: languageNames[locale.languageCode] ?? locale.languageCode,
        nativeName:
            nativeLanguageNames[locale.languageCode] ?? locale.languageCode,
        isRTL: locale.languageCode == 'ar',
      );
    }).toList();
  }

  /// Check if a language is currently selected
  bool isLanguageSelected(String languageCode) {
    return _currentLocale.languageCode == languageCode;
  }
}

/// Represents a language option in the language picker
class LanguageOption {
  final String code;
  final String name;
  final String nativeName;
  final bool isRTL;

  const LanguageOption({
    required this.code,
    required this.name,
    required this.nativeName,
    this.isRTL = false,
  });

  Locale get locale => Locale(code);

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is LanguageOption &&
          runtimeType == other.runtimeType &&
          code == other.code;

  @override
  int get hashCode => code.hashCode;

  @override
  String toString() => 'LanguageOption($code, $name)';
}
