import 'dart:io';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import 'package:dio/dio.dart';

import '../../models/document.dart';
import '../../providers/document_provider.dart';
// api_service not needed here; uploads use presigned URL via Dio

class DocumentUploadScreen extends StatefulWidget {
  const DocumentUploadScreen({super.key});

  @override
  State<DocumentUploadScreen> createState() => _DocumentUploadScreenState();
}

class _DocumentUploadScreenState extends State<DocumentUploadScreen> {
  DocumentType? _selectedType;
  final _titleCtrl = TextEditingController();
  final _descriptionCtrl = TextEditingController();
  DateTime? _expirationDate;
  PlatformFile? _pickedFile;

  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<DocumentProvider>(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Upload Document')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(controller: _titleCtrl, decoration: const InputDecoration(labelText: 'Title')),
            const SizedBox(height: 8),
            DropdownButton<DocumentType>(
              value: _selectedType,
              hint: const Text('Select document type'),
        items: DocumentType.values
          .map((t) => DropdownMenuItem(value: t, child: Text(Document.documentTypeToLabel(t))))
                  .toList(),
              onChanged: (v) => setState(() => _selectedType = v),
            ),
            const SizedBox(height: 8),
            TextField(controller: _descriptionCtrl, decoration: const InputDecoration(labelText: 'Description')),
            const SizedBox(height: 8),
            Row(
              children: [
                ElevatedButton(
                  child: const Text('Pick File'),
                  onPressed: () async {
                    final result = await FilePicker.platform.pickFiles(withData: false);
                    if (result != null && result.files.isNotEmpty) {
                      setState(() => _pickedFile = result.files.first);
                    }
                  },
                ),
                const SizedBox(width: 12),
                Expanded(child: Text(_pickedFile?.name ?? 'No file selected')),
              ],
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              child: const Text('Upload'),
              onPressed: provider.isLoading
                  ? null
                  : () async {
                      if (_pickedFile == null || _selectedType == null || _titleCtrl.text.isEmpty) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Fill required fields and pick a file')));
                        return;
                      }

                      // Request upload URL
                      final uploadRequest = DocumentUploadRequest(
                        title: _titleCtrl.text,
                        description: _descriptionCtrl.text,
                        documentType: _selectedType!,
                        expirationDate: _expirationDate,
                      );

                      final uploadResp = await provider.getUploadUrl(
                        request: uploadRequest,
                        fileExtension: _pickedFile!.extension ?? 'bin',
                        mimeType: _pickedFile!.name.endsWith('.pdf') ? 'application/pdf' : 'application/octet-stream',
                      );

                      if (uploadResp == null) {
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(provider.error ?? 'Upload init failed')));
                        return;
                      }

                      // Upload file via presigned URL
                      final filePath = _pickedFile!.path;
                      if (filePath == null) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Unable to read file')));
                        return;
                      }

                      final file = File(filePath);
                      try {
                        final bytes = await file.readAsBytes();
                        final dio = Dio();
                        await dio.put(
                          uploadResp.uploadUrl,
                          data: Stream.fromIterable([bytes]),
                          options: Options(headers: {'Content-Type': _pickedFile!.name.endsWith('.pdf') ? 'application/pdf' : 'application/octet-stream'}),
                        );
                      } catch (e) {
                        // If presigned upload failed, show message
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('File upload failed: $e')));
                        return;
                      }

                      // Complete upload
                      final completeReq = DocumentCompleteRequest(
                        storageKey: uploadResp.storageKey,
                        fileName: _pickedFile!.name,
                        fileSize: _pickedFile!.size,
                        mimeType: 'application/pdf',
                      );

                      final doc = await provider.completeUpload(metadata: uploadRequest, file: completeReq);
                      if (doc != null) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Upload complete')));
                        Navigator.of(context).pop();
                      } else {
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(provider.error ?? 'Failed to complete')));
                      }
                    },
            )
          ],
        ),
      ),
    );
  }
}
