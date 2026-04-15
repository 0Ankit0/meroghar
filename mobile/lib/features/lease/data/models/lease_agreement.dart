import 'package:equatable/equatable.dart';
import '../../../../core/utils/json_parsing.dart';
import '../../../applications/data/models/booking.dart';

class LeaseAgreement extends Equatable {
  final String id;
  final String bookingId;
  final String? templateId;
  final String? templateName;
  final String status;
  final String renderedContent;
  final String? eSignRequestId;
  final String? signedDocumentUrl;
  final String? previewUrl;
  final String? customerSignUrl;
  final DateTime? sentAt;
  final DateTime? customerSignedAt;
  final String? customerSignatureIp;
  final DateTime? ownerSignedAt;
  final String? ownerSignatureIp;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final String? summary;

  const LeaseAgreement({
    required this.id,
    required this.bookingId,
    required this.status,
    required this.renderedContent,
    this.templateId,
    this.templateName,
    this.eSignRequestId,
    this.signedDocumentUrl,
    this.previewUrl,
    this.customerSignUrl,
    this.sentAt,
    this.customerSignedAt,
    this.customerSignatureIp,
    this.ownerSignedAt,
    this.ownerSignatureIp,
    this.createdAt,
    this.updatedAt,
    this.summary,
  });

  factory LeaseAgreement.fromJson(Map<String, dynamic> json) {
    final nestedAgreement = readMap(json, ['agreement']);
    final source = nestedAgreement.isNotEmpty ? nestedAgreement : json;
    final template = readMap(source, ['template', 'agreement_template']);
    final links = readMap(source, ['links', 'urls', 'actions']);

    return LeaseAgreement(
      id: readString(source, ['id', 'agreement_id']) ?? '',
      bookingId: readString(source, ['bookingId', 'booking_id']) ??
          readString(json, ['bookingId', 'booking_id']) ??
          '',
      templateId: readString(source, ['templateId', 'template_id']) ??
          readString(template, ['id', 'template_id']),
      templateName:
          readString(template, ['name', 'title']) ?? readString(source, ['template_name']),
      status: normalizeAgreementStatusValue(
            readString(source, ['status', 'agreement_status']) ?? 'DRAFT',
          ) ??
          'DRAFT',
      renderedContent:
          readString(source, ['rendered_content', 'content', 'html', 'preview']) ??
              '',
      eSignRequestId:
          readString(source, ['esign_request_id', 'eSignRequestId']),
      signedDocumentUrl: readString(source, [
            'signed_document_url',
            'signedDocumentUrl',
            'document_url',
            'pdf_url',
          ]) ??
          readString(links, ['signed_document', 'document', 'pdf']),
      previewUrl: readString(source, [
            'preview_url',
            'agreement_url',
            'rendered_document_url',
            'renderedDocumentUrl',
            'url',
          ]) ??
          readString(links, ['preview', 'agreement']),
      customerSignUrl: readString(source, [
            'customer_sign_url',
            'tenant_sign_url',
            'sign_url',
            'signature_url',
            'esign_url',
          ]) ??
          readString(links, ['customer_sign', 'tenant_sign', 'sign']),
      sentAt: readDateTime(source, ['sent_at', 'sentAt']),
      customerSignedAt: readDateTime(source, [
        'customer_signed_at',
        'customerSignedAt',
        'tenant_signed_at',
        'tenantSignedAt',
      ]),
      customerSignatureIp: readString(source, [
        'customer_signature_ip',
        'customerSignatureIp',
        'tenant_signature_ip',
      ]),
      ownerSignedAt: readDateTime(source, [
        'owner_signed_at',
        'ownerSignedAt',
        'landlord_signed_at',
        'landlordSignedAt',
      ]),
      ownerSignatureIp: readString(source, [
        'owner_signature_ip',
        'ownerSignatureIp',
        'landlord_signature_ip',
      ]),
      createdAt: readDateTime(source, [
        'created_at',
        'createdAt',
        'generated_at',
        'generatedAt',
      ]),
      updatedAt: readDateTime(source, ['updated_at', 'updatedAt']),
      summary: readString(source, ['summary', 'note', 'description']),
    );
  }

  bool get isGenerated {
    return id.isNotEmpty ||
        renderedContent.trim().isNotEmpty ||
        signedDocumentUrl != null ||
        previewUrl != null;
  }

  bool get needsCustomerSignature => status == 'PENDING_CUSTOMER_SIGNATURE';
  bool get needsOwnerSignature => status == 'PENDING_OWNER_SIGNATURE';
  bool get canSendForSignature => status == 'DRAFT';
  bool get isSigned => status == 'SIGNED';
  String? get primaryDocumentUrl => signedDocumentUrl ?? previewUrl;

  @override
  List<Object?> get props => [
        id,
        bookingId,
        templateId,
        templateName,
        status,
        renderedContent,
        eSignRequestId,
        signedDocumentUrl,
        previewUrl,
        customerSignUrl,
        sentAt,
        customerSignedAt,
        customerSignatureIp,
        ownerSignedAt,
        ownerSignatureIp,
        createdAt,
        updatedAt,
        summary,
      ];
}
