/// Document model for file storage and management.
///
/// Implements T185 from tasks.md.
library;

enum DocumentType {
  leaseAgreement,
  idProof,
  incomeProof,
  policeVerification,
  rentReceipt,
  maintenanceBill,
  propertyDeed,
  taxReceipt,
  insurancePolicy,
  other,
}

enum DocumentStatus {
  active,
  expired,
  archived,
  deleted,
}

class Document {
  Document({
    required this.id,
    required this.title,
    this.description,
    required this.documentType,
    required this.status,
    required this.fileUrl,
    required this.fileName,
    required this.fileSize,
    required this.fileSizeMb,
    required this.mimeType,
    required this.storageKey,
    this.expirationDate,
    required this.isExpired,
    this.daysUntilExpiration,
    required this.needsReminder,
    required this.reminderSent,
    required this.reminderDaysBefore,
    required this.version,
    this.parentDocumentId,
    required this.uploadedBy,
    this.tenantId,
    this.propertyId,
    required this.createdAt,
    this.updatedAt,
  });

  factory Document.fromJson(Map<String, dynamic> json) {
    return Document(
      id: json['id'] as int,
      title: json['title'] as String,
      description: json['description'] as String?,
      documentType: documentTypeFromString(json['document_type'] as String),
      status: documentStatusFromString(json['status'] as String),
      fileUrl: json['file_url'] as String,
      fileName: json['file_name'] as String,
      fileSize: json['file_size'] as int,
      fileSizeMb: (json['file_size_mb'] as num).toDouble(),
      mimeType: json['mime_type'] as String,
      storageKey: json['storage_key'] as String,
      expirationDate: json['expiration_date'] != null
          ? DateTime.parse(json['expiration_date'] as String)
          : null,
      isExpired: json['is_expired'] as bool,
      daysUntilExpiration: json['days_until_expiration'] as int?,
      needsReminder: json['needs_reminder'] as bool,
      reminderSent: json['reminder_sent'] as bool,
      reminderDaysBefore: json['reminder_days_before'] as int,
      version: json['version'] as int,
      parentDocumentId: json['parent_document_id'] as int?,
      uploadedBy: json['uploaded_by'] as int,
      tenantId: json['tenant_id'] as int?,
      propertyId: json['property_id'] as int?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'] as String)
          : null,
    );
  }
  final int id;
  final String title;
  final String? description;
  final DocumentType documentType;
  final DocumentStatus status;
  final String fileUrl;
  final String fileName;
  final int fileSize;
  final double fileSizeMb;
  final String mimeType;
  final String storageKey;
  final DateTime? expirationDate;
  final bool isExpired;
  final int? daysUntilExpiration;
  final bool needsReminder;
  final bool reminderSent;
  final int reminderDaysBefore;
  final int version;
  final int? parentDocumentId;
  final int uploadedBy;
  final int? tenantId;
  final int? propertyId;
  final DateTime createdAt;
  final DateTime? updatedAt;

  // Computed properties
  bool get canRenew =>
      isExpired || (daysUntilExpiration != null && daysUntilExpiration! <= 30);
  bool get isActive => status == DocumentStatus.active;
  bool get isArchived => status == DocumentStatus.archived;
  bool get hasExpiration => expirationDate != null;
  bool get isLatestVersion => parentDocumentId == null;

  /// Get human-readable file size
  String get fileSizeFormatted {
    if (fileSizeMb < 1) {
      return '${(fileSizeMb * 1024).toStringAsFixed(0)} KB';
    } else {
      return '${fileSizeMb.toStringAsFixed(2)} MB';
    }
  }

  /// Get document type label
  String get typeLabel => documentTypeToLabel(documentType);

  /// Get status label
  String get statusLabel => documentStatusToLabel(status);

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'description': description,
        'document_type': documentTypeToString(documentType),
        'status': documentStatusToString(status),
        'file_url': fileUrl,
        'file_name': fileName,
        'file_size': fileSize,
        'file_size_mb': fileSizeMb,
        'mime_type': mimeType,
        'storage_key': storageKey,
        'expiration_date': expirationDate?.toIso8601String(),
        'is_expired': isExpired,
        'days_until_expiration': daysUntilExpiration,
        'needs_reminder': needsReminder,
        'reminder_sent': reminderSent,
        'reminder_days_before': reminderDaysBefore,
        'version': version,
        'parent_document_id': parentDocumentId,
        'uploaded_by': uploadedBy,
        'tenant_id': tenantId,
        'property_id': propertyId,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt?.toIso8601String(),
      };

  Document copyWith({
    int? id,
    String? title,
    String? description,
    DocumentType? documentType,
    DocumentStatus? status,
    String? fileUrl,
    String? fileName,
    int? fileSize,
    double? fileSizeMb,
    String? mimeType,
    String? storageKey,
    DateTime? expirationDate,
    bool? isExpired,
    int? daysUntilExpiration,
    bool? needsReminder,
    bool? reminderSent,
    int? reminderDaysBefore,
    int? version,
    int? parentDocumentId,
    int? uploadedBy,
    int? tenantId,
    int? propertyId,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) =>
      Document(
        id: id ?? this.id,
        title: title ?? this.title,
        description: description ?? this.description,
        documentType: documentType ?? this.documentType,
        status: status ?? this.status,
        fileUrl: fileUrl ?? this.fileUrl,
        fileName: fileName ?? this.fileName,
        fileSize: fileSize ?? this.fileSize,
        fileSizeMb: fileSizeMb ?? this.fileSizeMb,
        mimeType: mimeType ?? this.mimeType,
        storageKey: storageKey ?? this.storageKey,
        expirationDate: expirationDate ?? this.expirationDate,
        isExpired: isExpired ?? this.isExpired,
        daysUntilExpiration: daysUntilExpiration ?? this.daysUntilExpiration,
        needsReminder: needsReminder ?? this.needsReminder,
        reminderSent: reminderSent ?? this.reminderSent,
        reminderDaysBefore: reminderDaysBefore ?? this.reminderDaysBefore,
        version: version ?? this.version,
        parentDocumentId: parentDocumentId ?? this.parentDocumentId,
        uploadedBy: uploadedBy ?? this.uploadedBy,
        tenantId: tenantId ?? this.tenantId,
        propertyId: propertyId ?? this.propertyId,
        createdAt: createdAt ?? this.createdAt,
        updatedAt: updatedAt ?? this.updatedAt,
      );

  // Helper methods for enum conversion
  static DocumentType documentTypeFromString(String value) {
    switch (value) {
      case 'lease_agreement':
        return DocumentType.leaseAgreement;
      case 'id_proof':
        return DocumentType.idProof;
      case 'income_proof':
        return DocumentType.incomeProof;
      case 'police_verification':
        return DocumentType.policeVerification;
      case 'rent_receipt':
        return DocumentType.rentReceipt;
      case 'maintenance_bill':
        return DocumentType.maintenanceBill;
      case 'property_deed':
        return DocumentType.propertyDeed;
      case 'tax_receipt':
        return DocumentType.taxReceipt;
      case 'insurance_policy':
        return DocumentType.insurancePolicy;
      case 'other':
        return DocumentType.other;
      default:
        throw ArgumentError('Invalid document type: $value');
    }
  }

  static String documentTypeToString(DocumentType type) {
    switch (type) {
      case DocumentType.leaseAgreement:
        return 'lease_agreement';
      case DocumentType.idProof:
        return 'id_proof';
      case DocumentType.incomeProof:
        return 'income_proof';
      case DocumentType.policeVerification:
        return 'police_verification';
      case DocumentType.rentReceipt:
        return 'rent_receipt';
      case DocumentType.maintenanceBill:
        return 'maintenance_bill';
      case DocumentType.propertyDeed:
        return 'property_deed';
      case DocumentType.taxReceipt:
        return 'tax_receipt';
      case DocumentType.insurancePolicy:
        return 'insurance_policy';
      case DocumentType.other:
        return 'other';
    }
  }

  static String documentTypeToLabel(DocumentType type) {
    switch (type) {
      case DocumentType.leaseAgreement:
        return 'Lease Agreement';
      case DocumentType.idProof:
        return 'ID Proof';
      case DocumentType.incomeProof:
        return 'Income Proof';
      case DocumentType.policeVerification:
        return 'Police Verification';
      case DocumentType.rentReceipt:
        return 'Rent Receipt';
      case DocumentType.maintenanceBill:
        return 'Maintenance Bill';
      case DocumentType.propertyDeed:
        return 'Property Deed';
      case DocumentType.taxReceipt:
        return 'Tax Receipt';
      case DocumentType.insurancePolicy:
        return 'Insurance Policy';
      case DocumentType.other:
        return 'Other';
    }
  }

  static DocumentStatus documentStatusFromString(String value) {
    switch (value) {
      case 'active':
        return DocumentStatus.active;
      case 'expired':
        return DocumentStatus.expired;
      case 'archived':
        return DocumentStatus.archived;
      case 'deleted':
        return DocumentStatus.deleted;
      default:
        throw ArgumentError('Invalid document status: $value');
    }
  }

  static String documentStatusToString(DocumentStatus status) {
    switch (status) {
      case DocumentStatus.active:
        return 'active';
      case DocumentStatus.expired:
        return 'expired';
      case DocumentStatus.archived:
        return 'archived';
      case DocumentStatus.deleted:
        return 'deleted';
    }
  }

  static String documentStatusToLabel(DocumentStatus status) {
    switch (status) {
      case DocumentStatus.active:
        return 'Active';
      case DocumentStatus.expired:
        return 'Expired';
      case DocumentStatus.archived:
        return 'Archived';
      case DocumentStatus.deleted:
        return 'Deleted';
    }
  }
}

/// Request to initiate document upload
class DocumentUploadRequest {
  DocumentUploadRequest({
    required this.title,
    this.description,
    required this.documentType,
    this.expirationDate,
    this.reminderDaysBefore = 30,
    this.tenantId,
    this.propertyId,
  });
  final String title;
  final String? description;
  final DocumentType documentType;
  final DateTime? expirationDate;
  final int reminderDaysBefore;
  final int? tenantId;
  final int? propertyId;

  Map<String, dynamic> toJson() => {
        'title': title,
        'description': description,
        'document_type': Document.documentTypeToString(documentType),
        'expiration_date': expirationDate?.toIso8601String(),
        'reminder_days_before': reminderDaysBefore,
        'tenant_id': tenantId,
        'property_id': propertyId,
      };
}

/// Response from upload URL request
class DocumentUploadResponse {
  DocumentUploadResponse({
    required this.uploadUrl,
    required this.storageKey,
    required this.expiresIn,
    required this.maxFileSize,
    required this.allowedMimeTypes,
  });

  factory DocumentUploadResponse.fromJson(Map<String, dynamic> json) {
    return DocumentUploadResponse(
      uploadUrl: json['upload_url'] as String,
      storageKey: json['storage_key'] as String,
      expiresIn: json['expires_in'] as int,
      maxFileSize: json['max_file_size'] as int,
      allowedMimeTypes: (json['allowed_mime_types'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
    );
  }
  final String uploadUrl;
  final String storageKey;
  final int expiresIn;
  final int maxFileSize;
  final List<String> allowedMimeTypes;
}

/// Request to complete document upload
class DocumentCompleteRequest {
  DocumentCompleteRequest({
    required this.storageKey,
    required this.fileName,
    required this.fileSize,
    required this.mimeType,
  });
  final String storageKey;
  final String fileName;
  final int fileSize;
  final String mimeType;

  Map<String, dynamic> toJson() => {
        'storage_key': storageKey,
        'file_name': fileName,
        'file_size': fileSize,
        'mime_type': mimeType,
      };
}

/// Response with download URL
class DocumentDownloadResponse {
  DocumentDownloadResponse({
    required this.downloadUrl,
    required this.expiresIn,
    required this.fileName,
    required this.fileSize,
    required this.mimeType,
  });

  factory DocumentDownloadResponse.fromJson(Map<String, dynamic> json) {
    return DocumentDownloadResponse(
      downloadUrl: json['download_url'] as String,
      expiresIn: json['expires_in'] as int,
      fileName: json['file_name'] as String,
      fileSize: json['file_size'] as int,
      mimeType: json['mime_type'] as String,
    );
  }
  final String downloadUrl;
  final int expiresIn;
  final String fileName;
  final int fileSize;
  final String mimeType;
}

/// Paginated list of documents
class DocumentListResponse {
  DocumentListResponse({
    required this.documents,
    required this.total,
    required this.page,
    required this.pageSize,
  });

  factory DocumentListResponse.fromJson(Map<String, dynamic> json) {
    return DocumentListResponse(
      documents: (json['documents'] as List<dynamic>)
          .map((e) => Document.fromJson(e as Map<String, dynamic>))
          .toList(),
      total: json['total'] as int,
      page: json['page'] as int,
      pageSize: json['page_size'] as int,
    );
  }
  final List<Document> documents;
  final int total;
  final int page;
  final int pageSize;

  int get totalPages => (total / pageSize).ceil();
  bool get hasNextPage => page < totalPages;
  bool get hasPreviousPage => page > 1;
}
