import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/document_provider.dart';
import 'document_viewer_screen.dart';

class DocumentListScreen extends StatefulWidget {
  const DocumentListScreen({super.key});

  @override
  State<DocumentListScreen> createState() => _DocumentListScreenState();
}

class _DocumentListScreenState extends State<DocumentListScreen> {
  @override
  void initState() {
    super.initState();
    final provider = Provider.of<DocumentProvider>(context, listen: false);
    provider.fetchDocuments();
  }

  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<DocumentProvider>(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Documents')),
      body: provider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: provider.documents.length,
              itemBuilder: (context, idx) {
                final d = provider.documents[idx];
                return ListTile(
                  title: Text(d.title),
                  subtitle: Text('${d.typeLabel} • ${d.fileSizeFormatted}'),
                  trailing: d.isExpired
                      ? const Icon(Icons.warning, color: Colors.orange)
                      : null,
                  onTap: () async {
                    // Open viewer
                    Navigator.of(context).push(MaterialPageRoute(
                        builder: (_) => DocumentViewerScreen(document: d)));
                  },
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        child: const Icon(Icons.upload_file),
        onPressed: () => Navigator.of(context).pushNamed('/documents/upload'),
      ),
    );
  }
}
