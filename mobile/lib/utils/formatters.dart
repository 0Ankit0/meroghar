import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

/// Locale-specific number and currency formatters
///
/// Implements T218 from tasks.md.
///
/// Provides formatting utilities for:
/// - Currency amounts with proper symbols and decimal places
/// - Numbers with locale-specific grouping and decimal separators
/// - Dates and times in locale format
/// - Percentages
/// - File sizes
///
/// Usage:
/// ```dart
/// final formatter = LocaleFormatter(locale: Locale('hi'));
/// print(formatter.formatCurrency(1000.50)); // ₹1,000.50
/// print(formatter.formatNumber(1234567)); // 12,34,567 (Indian format)
/// ```
class LocaleFormatter {
  LocaleFormatter({required this.locale});
  final Locale locale;

  /// Currency symbols for supported locales
  static const Map<String, String> currencySymbols = {
    'en': '\$', // US Dollar (default)
    'hi': '₹', // Indian Rupee
    'es': '€', // Euro
    'ar': 'د.إ', // UAE Dirham
  };

  /// Currency codes for supported locales
  static const Map<String, String> currencyCodes = {
    'en': 'USD',
    'hi': 'INR',
    'es': 'EUR',
    'ar': 'AED',
  };

  /// Get currency symbol for current locale
  String get currencySymbol =>
      currencySymbols[locale.languageCode] ?? currencySymbols['en']!;

  /// Get currency code for current locale
  String get currencyCode =>
      currencyCodes[locale.languageCode] ?? currencyCodes['en']!;

  /// Format currency amount with proper symbol and decimal places
  ///
  /// [amount] - Amount to format
  /// [showSymbol] - Whether to show currency symbol (default: true)
  /// [showCode] - Whether to show currency code (default: false)
  ///
  /// Examples:
  /// - en: $1,234.56
  /// - hi: ₹1,234.56
  /// - es: €1.234,56
  /// - ar: د.إ 1,234.56
  String formatCurrency(
    double amount, {
    bool showSymbol = true,
    bool showCode = false,
  }) {
    final formatter = NumberFormat.currency(
      locale: _getLocaleString(),
      symbol: showSymbol ? currencySymbol : '',
      decimalDigits: 2,
    );

    final formatted = formatter.format(amount);

    if (showCode) {
      return '$formatted $currencyCode';
    }

    return formatted;
  }

  /// Format currency amount in compact form (e.g., 1.2K, 3.4M)
  ///
  /// Useful for displaying large amounts in limited space
  String formatCurrencyCompact(double amount) {
    final formatter = NumberFormat.compactCurrency(
      locale: _getLocaleString(),
      symbol: currencySymbol,
      decimalDigits: 1,
    );

    return formatter.format(amount);
  }

  /// Format number with locale-specific grouping and decimal separators
  ///
  /// Examples:
  /// - en: 1,234,567.89
  /// - hi: 12,34,567.89 (Indian numbering system)
  /// - es: 1.234.567,89
  /// - ar: 1,234,567.89
  String formatNumber(
    num number, {
    int? decimalDigits,
  }) {
    final formatter = NumberFormat.decimalPattern(_getLocaleString());

    if (decimalDigits != null) {
      formatter.minimumFractionDigits = decimalDigits;
      formatter.maximumFractionDigits = decimalDigits;
    }

    return formatter.format(number);
  }

  /// Format number in compact form (e.g., 1.2K, 3.4M)
  String formatNumberCompact(num number) {
    final formatter = NumberFormat.compact(locale: _getLocaleString());
    return formatter.format(number);
  }

  /// Format percentage with locale-specific decimal separator
  ///
  /// [value] - Value between 0 and 1 (e.g., 0.15 for 15%)
  /// [decimalDigits] - Number of decimal places (default: 1)
  String formatPercentage(
    double value, {
    int decimalDigits = 1,
  }) {
    final formatter = NumberFormat.percentPattern(_getLocaleString());
    formatter.minimumFractionDigits = decimalDigits;
    formatter.maximumFractionDigits = decimalDigits;

    return formatter.format(value);
  }

  /// Format date in locale-specific format
  ///
  /// [date] - Date to format
  /// [format] - Date format (default: medium)
  ///
  /// Available formats:
  /// - short: 1/1/24
  /// - medium: Jan 1, 2024
  /// - long: January 1, 2024
  /// - full: Monday, January 1, 2024
  String formatDate(
    DateTime date, {
    String format = 'medium',
  }) {
    final localeString = _getLocaleString();

    switch (format) {
      case 'short':
        return DateFormat.yMd(localeString).format(date);
      case 'medium':
        return DateFormat.yMMMd(localeString).format(date);
      case 'long':
        return DateFormat.yMMMMd(localeString).format(date);
      case 'full':
        return DateFormat.yMMMMEEEEd(localeString).format(date);
      default:
        return DateFormat.yMMMd(localeString).format(date);
    }
  }

  /// Format time in locale-specific format
  ///
  /// [time] - Time to format
  /// [includeSeconds] - Whether to include seconds (default: false)
  String formatTime(
    DateTime time, {
    bool includeSeconds = false,
  }) {
    final localeString = _getLocaleString();

    if (includeSeconds) {
      return DateFormat.Hms(localeString).format(time);
    } else {
      return DateFormat.Hm(localeString).format(time);
    }
  }

  /// Format date and time in locale-specific format
  String formatDateTime(
    DateTime dateTime, {
    String dateFormat = 'medium',
    bool includeSeconds = false,
  }) {
    final date = formatDate(dateTime, format: dateFormat);
    final time = formatTime(dateTime, includeSeconds: includeSeconds);

    return '$date $time';
  }

  /// Format relative date (e.g., "Today", "Yesterday", "2 days ago")
  String formatRelativeDate(DateTime date) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final dateOnly = DateTime(date.year, date.month, date.day);

    if (dateOnly == today) {
      return 'Today';
    } else if (dateOnly == yesterday) {
      return 'Yesterday';
    } else if (dateOnly.isAfter(today.subtract(const Duration(days: 7)))) {
      // Within last week
      return DateFormat.EEEE(_getLocaleString()).format(date);
    } else if (dateOnly.isAfter(today.subtract(const Duration(days: 30)))) {
      // Within last month
      final days = today.difference(dateOnly).inDays;
      return '$days days ago';
    } else {
      return formatDate(date, format: 'short');
    }
  }

  /// Format file size in human-readable format
  ///
  /// [bytes] - File size in bytes
  ///
  /// Examples:
  /// - 1024 -> 1.0 KB
  /// - 1048576 -> 1.0 MB
  /// - 1073741824 -> 1.0 GB
  String formatFileSize(int bytes) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    var size = bytes.toDouble();
    var unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return '${formatNumber(size, decimalDigits: 1)} ${units[unitIndex]}';
  }

  /// Format duration in human-readable format
  ///
  /// [duration] - Duration to format
  ///
  /// Examples:
  /// - Duration(hours: 2, minutes: 30) -> "2h 30m"
  /// - Duration(minutes: 45) -> "45m"
  /// - Duration(seconds: 30) -> "30s"
  String formatDuration(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes.remainder(60);
    final seconds = duration.inSeconds.remainder(60);

    final parts = <String>[];

    if (hours > 0) parts.add('${hours}h');
    if (minutes > 0) parts.add('${minutes}m');
    if (seconds > 0 && hours == 0) parts.add('${seconds}s');

    return parts.isEmpty ? '0s' : parts.join(' ');
  }

  /// Get locale string in format "language_COUNTRY"
  String _getLocaleString() {
    // Map locale to proper locale string with country code
    switch (locale.languageCode) {
      case 'en':
        return 'en_US';
      case 'hi':
        return 'hi_IN';
      case 'es':
        return 'es_ES';
      case 'ar':
        return 'ar_AE';
      default:
        return 'en_US';
    }
  }
}

/// Extension on BuildContext to easily access LocaleFormatter
extension FormatterExtension on BuildContext {
  LocaleFormatter get formatter => LocaleFormatter(
        locale: Localizations.localeOf(this),
      );
}

/// Helper functions for quick formatting without creating formatter instance
class FormatHelpers {
  /// Format currency for a specific locale
  static String formatCurrency(
    double amount,
    Locale locale, {
    bool showSymbol = true,
  }) =>
      LocaleFormatter(locale: locale).formatCurrency(
        amount,
        showSymbol: showSymbol,
      );

  /// Format number for a specific locale
  static String formatNumber(
    num number,
    Locale locale, {
    int? decimalDigits,
  }) =>
      LocaleFormatter(locale: locale).formatNumber(
        number,
        decimalDigits: decimalDigits,
      );

  /// Format date for a specific locale
  static String formatDate(
    DateTime date,
    Locale locale, {
    String format = 'medium',
  }) =>
      LocaleFormatter(locale: locale).formatDate(
        date,
        format: format,
      );
}
