/// Receipt view screen for displaying and managing payment receipts.
///
/// Implements T070 from tasks.md.
library;

import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:pdfrx/pdfrx.dart';
import 'package:provider/provider.dart';
import 'package:share_plus/share_plus.dart';

import '../../providers/payment_provider.dart';

class ReceiptViewScreen extends StatefulWidget {
  final String paymentId;
  final String? tenantName;

  const ReceiptViewScreen({
    super.key,
    required this.paymentId,
    this.tenantName,
  });

  @override
  State<ReceiptViewScreen> createState() => _ReceiptViewScreenState();
}

class _ReceiptViewScreenState extends State<ReceiptViewScreen> {
  bool _isLoading = true;
  String? _errorMessage;
  Uint8List? _pdfData;
  String? _savedFilePath;

  @override
  void initState() {
    super.initState();
    _loadReceipt();
  }

  Future<void> _loadReceipt() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final paymentProvider = context.read<PaymentProvider>();
      // TODO: Update PaymentProvider.downloadReceipt to return Uint8List
      // For now, we'll create a placeholder implementation
      final result = await paymentProvider.downloadReceipt(widget.paymentId);

      if (result != null) {
        // Convert the result to Uint8List (placeholder for actual PDF data)
        // In production, the API should return the PDF bytes directly
        setState(() {
          _pdfData = Uint8List(0); // Empty PDF data as placeholder
          _errorMessage = 'PDF download not yet implemented in backend';
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = 'Failed to download receipt';
          _isLoading = false;
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = 'Error: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _saveToDevice() async {
    if (_pdfData == null) return;

    try {
      // Get the downloads directory
      Directory? directory;
      if (Platform.isAndroid) {
        directory = await getExternalStorageDirectory();
      } else if (Platform.isIOS) {
        directory = await getApplicationDocumentsDirectory();
      } else {
        directory = await getDownloadsDirectory();
      }

      if (directory == null) {
        throw Exception('Could not access storage directory');
      }

      // Create filename with timestamp
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final fileName = 'receipt_${widget.paymentId}_$timestamp.pdf';
      final filePath = '${directory.path}/$fileName';

      // Write PDF data to file
      final file = File(filePath);
      await file.writeAsBytes(_pdfData!);

      setState(() {
        _savedFilePath = filePath;
      });

      if (!mounted) return;

      // Show success message
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Receipt saved to $filePath'),
          backgroundColor: Colors.green,
          action: SnackBarAction(
            label: 'SHARE',
            textColor: Colors.white,
            onPressed: _shareReceipt,
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to save receipt: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _shareReceipt() async {
    if (_pdfData == null) return;

    try {
      // Create a temporary file for sharing
      final tempDir = await getTemporaryDirectory();
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final fileName = 'receipt_${widget.paymentId}_$timestamp.pdf';
      final filePath = '${tempDir.path}/$fileName';

      // Write PDF data to temporary file
      final file = File(filePath);
      await file.writeAsBytes(_pdfData!);

      // Share the file using SharePlus
      await SharePlus.instance.share(
        ShareParams(
          files: [XFile(filePath)],
          subject: widget.tenantName != null
              ? 'Payment Receipt - ${widget.tenantName}'
              : 'Payment Receipt',
          text:
              'Payment receipt for transaction ${widget.paymentId.substring(0, 8)}',
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to share receipt: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Payment Receipt'),
        actions: [
          if (_pdfData != null) ...[
            IconButton(
              icon: const Icon(Icons.share),
              onPressed: _shareReceipt,
              tooltip: 'Share Receipt',
            ),
            IconButton(
              icon: const Icon(Icons.download),
              onPressed: _saveToDevice,
              tooltip: 'Save to Device',
            ),
          ],
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadReceipt,
            tooltip: 'Reload Receipt',
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Loading receipt...'),
          ],
        ),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: Colors.red.shade300),
            const SizedBox(height: 16),
            Text(
              _errorMessage!,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _loadReceipt,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_pdfData == null) {
      return const Center(
        child: Text('No receipt data available'),
      );
    }

    return Column(
      children: [
        // PDF Viewer
        Expanded(
          child: PdfViewer.data(
            _pdfData!,
            sourceName: 'receipt_${widget.paymentId}.pdf',
            params: const PdfViewerParams(
              margin: 8,
              minScale: 0.5,
              maxScale: 4.0,
              panEnabled: true,
              scaleEnabled: true,
            ),
          ),
        ),
        // Bottom info bar
        if (_savedFilePath != null)
          Container(
            padding: const EdgeInsets.all(12),
            color: Colors.green.shade50,
            child: Row(
              children: [
                Icon(Icons.check_circle, color: Colors.green.shade700),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Saved to device',
                    style: TextStyle(
                      color: Colors.green.shade700,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                TextButton(
                  onPressed: _shareReceipt,
                  child: const Text('SHARE'),
                ),
              ],
            ),
          ),
      ],
    );
  }
}
