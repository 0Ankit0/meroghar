import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../models/document.dart';

class DocumentViewerScreen extends StatelessWidget {
  final Document document;

  const DocumentViewerScreen({super.key, required this.document});

  @override
  Widget build(BuildContext context) {
    // Simple viewer: show the file URL with copy action. In production use a PDF viewer.
    return Scaffold(
      appBar: AppBar(title: Text(document.title)),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Document URL:',
                style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            SelectableText(document.fileUrl),
            const SizedBox(height: 16),
            Row(children: [
              ElevatedButton(
                onPressed: () async {
                  await Clipboard.setData(
                      ClipboardData(text: document.fileUrl));
                  ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('URL copied to clipboard')));
                },
                child: const Text('Copy URL'),
              ),
            ])
          ],
        ),
      ),
    );
  }
}
