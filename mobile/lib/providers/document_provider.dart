/// Document provider for upload, listing and download functionality.
///
/// Implements T186 from tasks.md.
library;

import 'package:flutter/foundation.dart';

import '../models/document.dart';
import '../services/api_service.dart';

class DocumentProvider with ChangeNotifier {
  DocumentProvider(this._apiService);
  final ApiService _apiService;

  List<Document> _documents = [];
  bool _isLoading = false;
  String? _error;

  List<Document> get documents => _documents;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<DocumentUploadResponse?> getUploadUrl({
    required DocumentUploadRequest request,
    required String fileExtension,
    required String mimeType,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.post('/documents/upload-url',
          data: request.toJson(),
          queryParameters: {
            'file_extension': fileExtension,
            'mime_type': mimeType,
          });

      _isLoading = false;
      if (response.success) {
        final data = response.data as Map<String, dynamic>;
        notifyListeners();
        return DocumentUploadResponse.fromJson(data);
      } else {
        _error = response.message ?? 'Failed to get upload url';
        notifyListeners();
        return null;
      }
    } catch (e) {
      _error = 'Network error: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  Future<Document?> completeUpload({
    required DocumentUploadRequest metadata,
    required DocumentCompleteRequest file,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final body = metadata.toJson();
      body.addAll(file.toJson());

      final response = await _apiService.post('/documents', data: body);

      _isLoading = false;
      if (response.success && response.statusCode == 201) {
        final data = response.data as Map<String, dynamic>;
        final doc = Document.fromJson(data);
        _documents.insert(0, doc);
        notifyListeners();
        return doc;
      } else {
        _error = response.message ?? 'Failed to complete upload';
        notifyListeners();
        return null;
      }
    } catch (e) {
      _error = 'Network error: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  Future<DocumentDownloadResponse?> getDownloadUrl(int documentId) async {
    try {
      final response = await _apiService.get('/documents/$documentId/download');
      if (response.success) {
        return DocumentDownloadResponse.fromJson(
            response.data as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      _error = 'Network error: ${e.toString()}';
      notifyListeners();
      return null;
    }
  }

  Future<void> fetchDocuments({
    DocumentType? type,
    DocumentStatus? status,
    int? tenantId,
    int page = 1,
    int pageSize = 20,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final query = <String, dynamic>{'page': page, 'page_size': pageSize};
      if (type != null) {
        query['document_type'] = Document.documentTypeToString(type);
      }
      if (status != null) {
        query['status'] = Document.documentStatusToString(status);
      }
      if (tenantId != null) query['tenant_id'] = tenantId;

      final response =
          await _apiService.get('/documents', queryParameters: query);
      _isLoading = false;
      if (response.success) {
        final data = response.data as Map<String, dynamic>;
        final docs = (data['documents'] as List)
            .map((e) => Document.fromJson(e as Map<String, dynamic>))
            .toList();
        _documents = docs;
        notifyListeners();
      } else {
        _error = response.message ?? 'Failed to fetch documents';
        notifyListeners();
      }
    } catch (e) {
      _error = 'Network error: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<Document?> getDocument(int id) async {
    try {
      final response = await _apiService.get('/documents/$id');
      if (response.success) {
        return Document.fromJson(response.data as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      _error = 'Network error: ${e.toString()}';
      notifyListeners();
      return null;
    }
  }

  Future<bool> deleteDocument(int id, {bool hardDelete = false}) async {
    try {
      final response = await _apiService.delete('/documents/$id',
          queryParameters: {'hard_delete': hardDelete});
      if (response.success) {
        _documents.removeWhere((d) => d.id == id);
        notifyListeners();
        return true;
      }
      _error = response.message ?? 'Failed to delete document';
      notifyListeners();
      return false;
    } catch (e) {
      _error = 'Network error: ${e.toString()}';
      notifyListeners();
      return false;
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
