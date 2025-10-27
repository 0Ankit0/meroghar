/// Export provider with history tracking for payment exports.
///
/// Implements T210 from tasks.md.
library;

import 'package:flutter/foundation.dart';

import '../services/file_service.dart';

/// Format for exported files.
enum ExportFormat {
  excel('excel', 'xlsx'),
  pdf('pdf', 'pdf'),
  csv('csv', 'csv');

  const ExportFormat(this.value, this.extension);
  final String value;
  final String extension;
}

/// Status of an export operation.
enum ExportStatus {
  pending,
  downloading,
  completed,
  failed,
}

/// Information about an export operation.
class ExportHistoryEntry {
  final String id;
  final String title;
  final ExportFormat format;
  final DateTime createdAt;
  final ExportStatus status;
  final String? filePath;
  final String? error;
  final int? fileSize;

  ExportHistoryEntry({
    required this.id,
    required this.title,
    required this.format,
    required this.createdAt,
    required this.status,
    this.filePath,
    this.error,
    this.fileSize,
  });

  ExportHistoryEntry copyWith({
    String? id,
    String? title,
    ExportFormat? format,
    DateTime? createdAt,
    ExportStatus? status,
    String? filePath,
    String? error,
    int? fileSize,
  }) {
    return ExportHistoryEntry(
      id: id ?? this.id,
      title: title ?? this.title,
      format: format ?? this.format,
      createdAt: createdAt ?? this.createdAt,
      status: status ?? this.status,
      filePath: filePath ?? this.filePath,
      error: error ?? this.error,
      fileSize: fileSize ?? this.fileSize,
    );
  }
}

/// Provider for managing payment export operations and history.
class ExportProvider with ChangeNotifier {
  final FileService _fileService;

  final List<ExportHistoryEntry> _history = [];
  bool _isExporting = false;
  String? _error;
  double _downloadProgress = 0.0;

  List<ExportHistoryEntry> get history => List.unmodifiable(_history);
  bool get isExporting => _isExporting;
  String? get error => _error;
  double get downloadProgress => _downloadProgress;

  ExportProvider(this._fileService);

  /// Export payment history for the current user.
  ///
  /// [startDate] - Start date for payment history
  /// [endDate] - End date for payment history
  /// [format] - Export format (Excel or PDF)
  /// [tenantId] - Optional tenant ID for filtering
  Future<String?> exportPaymentHistory({
    required DateTime startDate,
    required DateTime endDate,
    required ExportFormat format,
    int? tenantId,
  }) async {
    _isExporting = true;
    _error = null;
    _downloadProgress = 0.0;
    notifyListeners();

    // Create export entry
    final exportId = DateTime.now().millisecondsSinceEpoch.toString();
    final fileName =
        'payment_history_${startDate.year}${startDate.month}_${endDate.year}${endDate.month}.${format.extension}';

    final entry = ExportHistoryEntry(
      id: exportId,
      title:
          'Payment History (${_formatDate(startDate)} - ${_formatDate(endDate)})',
      format: format,
      createdAt: DateTime.now(),
      status: ExportStatus.downloading,
    );

    _history.insert(0, entry);
    notifyListeners();

    try {
      // Prepare query parameters
      final queryParams = <String, dynamic>{
        'start_date': startDate.toIso8601String().split('T')[0],
        'end_date': endDate.toIso8601String().split('T')[0],
        'format': format.value,
      };

      if (tenantId != null) {
        queryParams['tenant_id'] = tenantId;
      }

      // Download file
      final filePath = await _fileService.downloadFromApi(
        '/api/v1/payments/export',
        fileName: fileName,
        queryParameters: queryParams,
        onProgress: (progress) {
          _downloadProgress = progress;
          notifyListeners();
        },
      );

      if (filePath != null) {
        // Get file size
        final fileSize = await _fileService.getFileSize(filePath);

        // Update history entry
        final index = _history.indexWhere((e) => e.id == exportId);
        if (index >= 0) {
          _history[index] = entry.copyWith(
            status: ExportStatus.completed,
            filePath: filePath,
            fileSize: fileSize,
          );
        }

        _isExporting = false;
        notifyListeners();

        return filePath;
      } else {
        throw Exception('Failed to download export file');
      }
    } catch (e) {
      _error = 'Export failed: ${e.toString()}';

      // Update history entry
      final index = _history.indexWhere((e) => e.id == exportId);
      if (index >= 0) {
        _history[index] = entry.copyWith(
          status: ExportStatus.failed,
          error: _error,
        );
      }

      _isExporting = false;
      notifyListeners();

      return null;
    }
  }

  /// Share an export file with other apps.
  Future<bool> shareExport(ExportHistoryEntry entry) async {
    if (entry.filePath == null) {
      _error = 'File not found';
      notifyListeners();
      return false;
    }

    try {
      final result = await _fileService.shareFile(
        entry.filePath!,
        subject: entry.title,
        text: 'Payment history export from MeroGhar',
      );

      if (!result) {
        _error = 'Failed to share file';
        notifyListeners();
      }

      return result;
    } catch (e) {
      _error = 'Error sharing file: ${e.toString()}';
      notifyListeners();
      return false;
    }
  }

  /// Delete an export file and remove from history.
  Future<bool> deleteExport(ExportHistoryEntry entry) async {
    try {
      // Delete file if it exists
      if (entry.filePath != null) {
        await _fileService.deleteFile(entry.filePath!);
      }

      // Remove from history
      _history.removeWhere((e) => e.id == entry.id);
      notifyListeners();

      return true;
    } catch (e) {
      _error = 'Error deleting export: ${e.toString()}';
      notifyListeners();
      return false;
    }
  }

  /// Clear all export history and delete files.
  Future<bool> clearHistory() async {
    try {
      // Delete all files
      for (final entry in _history) {
        if (entry.filePath != null) {
          await _fileService.deleteFile(entry.filePath!);
        }
      }

      // Clear history
      _history.clear();
      notifyListeners();

      return true;
    } catch (e) {
      _error = 'Error clearing history: ${e.toString()}';
      notifyListeners();
      return false;
    }
  }

  /// Get total size of all exported files.
  int get totalExportSize {
    return _history.fold<int>(
      0,
      (sum, entry) => sum + (entry.fileSize ?? 0),
    );
  }

  /// Get count of completed exports.
  int get completedExportCount {
    return _history.where((e) => e.status == ExportStatus.completed).length;
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }
}
