import 'package:flutter/material.dart';

/// Dialog widget to view receipt images
class ReceiptViewerDialog extends StatelessWidget {
  const ReceiptViewerDialog({
    Key? key,
    required this.receiptUrl,
    required this.expenseName,
  }) : super(key: key);
  final String receiptUrl;
  final String expenseName;

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: Text('Receipt: $expenseName'),
          actions: [
            IconButton(
              icon: const Icon(Icons.download),
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                      content: Text('Download functionality coming soon')),
                );
              },
            ),
          ],
        ),
        body: Center(
          child: receiptUrl.isEmpty
              ? const Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.receipt_long, size: 64, color: Colors.grey),
                    SizedBox(height: 16),
                    Text('No receipt available'),
                  ],
                )
              : InteractiveViewer(
                  child: Image.network(
                    receiptUrl,
                    loadingBuilder: (context, child, loadingProgress) {
                      if (loadingProgress == null) return child;
                      return Center(
                        child: CircularProgressIndicator(
                          value: loadingProgress.expectedTotalBytes != null
                              ? loadingProgress.cumulativeBytesLoaded /
                                  loadingProgress.expectedTotalBytes!
                              : null,
                        ),
                      );
                    },
                    errorBuilder: (context, error, stackTrace) {
                      return const Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.error_outline,
                              size: 64, color: Colors.red),
                          SizedBox(height: 16),
                          Text('Failed to load receipt'),
                        ],
                      );
                    },
                  ),
                ),
        ),
      );
}
