/// File download and sharing service for mobile app.
///
/// Implements T209 from tasks.md.
library;

import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import 'api_service.dart';

/// Service for handling file downloads and sharing.
///
/// Features:
/// - Download files from API
/// - Save files to device storage
/// - Share files with other apps
/// - Track download progress
/// - Handle different file types
class FileService {
  factory FileService() => instance;

  FileService._internal();
  static final FileService instance = FileService._internal();

  final ApiService _apiService = ApiService.instance;

  /// Download a file from the given URL and save it to device storage.
  ///
  /// Returns the local file path on success, null on failure.
  ///
  /// [url] - The URL to download from (can be relative or absolute)
  /// [fileName] - The name to save the file as
  /// [onProgress] - Optional callback for download progress (0.0 to 1.0)
  Future<String?> downloadFile(
    String url, {
    required String fileName,
    Function(double progress)? onProgress,
  }) async {
    try {
      // Get the downloads directory
      final directory = await getApplicationDocumentsDirectory();
      final downloadsDir = Directory('${directory.path}/downloads');

      // Create downloads directory if it doesn't exist
      if (!await downloadsDir.exists()) {
        await downloadsDir.create(recursive: true);
      }

      final filePath = '${downloadsDir.path}/$fileName';

      // Download the file using ApiService
      final response = await _apiService.downloadFile(
        url,
        filePath,
        onReceiveProgress: (received, total) {
          if (total != -1 && onProgress != null) {
            final progress = received / total;
            onProgress(progress);
          }
        },
      );

      if (response.isSuccess) {
        return filePath;
      } else {
        print('Failed to download file: ${response.message}');
        return null;
      }
    } catch (e) {
      print('Error downloading file: $e');
      return null;
    }
  }

  /// Download a file from an API endpoint and save it to device storage.
  ///
  /// Returns the local file path on success, null on failure.
  ///
  /// [endpoint] - The API endpoint path
  /// [fileName] - The name to save the file as
  /// [queryParameters] - Optional query parameters
  /// [onProgress] - Optional callback for download progress (0.0 to 1.0)
  Future<String?> downloadFromApi(
    String endpoint, {
    required String fileName,
    Map<String, dynamic>? queryParameters,
    Function(double progress)? onProgress,
  }) async {
    try {
      // Get the downloads directory
      final directory = await getApplicationDocumentsDirectory();
      final downloadsDir = Directory('${directory.path}/downloads');

      // Create downloads directory if it doesn't exist
      if (!await downloadsDir.exists()) {
        await downloadsDir.create(recursive: true);
      }

      final filePath = '${downloadsDir.path}/$fileName';

      // Download using API service
      final response = await _apiService.downloadFile(
        endpoint,
        filePath,
        onReceiveProgress: (received, total) {
          if (total != -1 && onProgress != null) {
            final progress = received / total;
            onProgress(progress);
          }
        },
        queryParameters: queryParameters,
      );

      if (response.isSuccess) {
        return filePath;
      } else {
        print('Failed to download from API: ${response.message}');
        return null;
      }
    } catch (e) {
      print('Error downloading from API: $e');
      return null;
    }
  }

  /// Share a file with other apps using the system share dialog.
  ///
  /// [filePath] - The local path to the file to share
  /// [subject] - Optional subject/title for the share
  /// [text] - Optional text to include with the share
  Future<bool> shareFile(
    String filePath, {
    String? subject,
    String? text,
  }) async {
    try {
      final file = File(filePath);
      if (!await file.exists()) {
        print('File does not exist: $filePath');
        return false;
      }

      final xFile = XFile(filePath);
      final result = await Share.shareXFiles(
        [xFile],
        subject: subject,
        text: text,
      );

      return result.status == ShareResultStatus.success;
    } catch (e) {
      print('Error sharing file: $e');
      return false;
    }
  }

  /// Share multiple files with other apps.
  ///
  /// [filePaths] - List of local file paths to share
  /// [subject] - Optional subject/title for the share
  /// [text] - Optional text to include with the share
  Future<bool> shareFiles(
    List<String> filePaths, {
    String? subject,
    String? text,
  }) async {
    try {
      final xFiles = <XFile>[];

      for (final path in filePaths) {
        final file = File(path);
        if (await file.exists()) {
          xFiles.add(XFile(path));
        }
      }

      if (xFiles.isEmpty) {
        print('No valid files to share');
        return false;
      }

      final result = await Share.shareXFiles(
        xFiles,
        subject: subject,
        text: text,
      );

      return result.status == ShareResultStatus.success;
    } catch (e) {
      print('Error sharing files: $e');
      return false;
    }
  }

  /// Get the size of a file in bytes.
  Future<int?> getFileSize(String filePath) async {
    try {
      final file = File(filePath);
      if (await file.exists()) {
        return await file.length();
      }
      return null;
    } catch (e) {
      print('Error getting file size: $e');
      return null;
    }
  }

  /// Delete a file from device storage.
  Future<bool> deleteFile(String filePath) async {
    try {
      final file = File(filePath);
      if (await file.exists()) {
        await file.delete();
        return true;
      }
      return false;
    } catch (e) {
      print('Error deleting file: $e');
      return false;
    }
  }

  /// Get a list of all downloaded files.
  Future<List<FileInfo>> listDownloadedFiles() async {
    try {
      final directory = await getApplicationDocumentsDirectory();
      final downloadsDir = Directory('${directory.path}/downloads');

      if (!await downloadsDir.exists()) {
        return [];
      }

      final files = downloadsDir.listSync();
      final fileInfos = <FileInfo>[];

      for (final file in files) {
        if (file is File) {
          final stat = await file.stat();
          fileInfos.add(FileInfo(
            path: file.path,
            name: file.path.split('/').last,
            size: stat.size,
            modifiedDate: stat.modified,
          ));
        }
      }

      // Sort by modified date (newest first)
      fileInfos.sort((a, b) => b.modifiedDate.compareTo(a.modifiedDate));

      return fileInfos;
    } catch (e) {
      print('Error listing downloaded files: $e');
      return [];
    }
  }

  /// Clear all downloaded files.
  Future<bool> clearDownloads() async {
    try {
      final directory = await getApplicationDocumentsDirectory();
      final downloadsDir = Directory('${directory.path}/downloads');

      if (await downloadsDir.exists()) {
        await downloadsDir.delete(recursive: true);
        return true;
      }
      return false;
    } catch (e) {
      print('Error clearing downloads: $e');
      return false;
    }
  }

  /// Format file size for display (e.g., "1.5 MB")
  static String formatFileSize(int bytes) {
    if (bytes < 1024) {
      return '$bytes B';
    } else if (bytes < 1024 * 1024) {
      return '${(bytes / 1024).toStringAsFixed(1)} KB';
    } else if (bytes < 1024 * 1024 * 1024) {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    } else {
      return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
    }
  }

  /// Get file extension from file name.
  static String getFileExtension(String fileName) {
    final parts = fileName.split('.');
    return parts.length > 1 ? parts.last.toLowerCase() : '';
  }

  /// Get MIME type from file extension.
  static String getMimeType(String fileName) {
    final extension = getFileExtension(fileName);
    switch (extension) {
      case 'pdf':
        return 'application/pdf';
      case 'xlsx':
      case 'xls':
        return 'application/vnd.ms-excel';
      case 'csv':
        return 'text/csv';
      case 'jpg':
      case 'jpeg':
        return 'image/jpeg';
      case 'png':
        return 'image/png';
      case 'txt':
        return 'text/plain';
      case 'json':
        return 'application/json';
      default:
        return 'application/octet-stream';
    }
  }
}

/// Information about a downloaded file.
class FileInfo {
  FileInfo({
    required this.path,
    required this.name,
    required this.size,
    required this.modifiedDate,
  });
  final String path;
  final String name;
  final int size;
  final DateTime modifiedDate;

  String get formattedSize => FileService.formatFileSize(size);
  String get extension => FileService.getFileExtension(name);
  String get mimeType => FileService.getMimeType(name);
}
