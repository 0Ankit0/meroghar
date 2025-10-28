import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

/// Payment gateway screen with webview integration for Khalti, eSewa, and IME Pay.
///
/// Implements T119 from tasks.md.
///
/// This screen:
/// 1. Displays payment gateway URL in a webview
/// 2. Intercepts callback URLs to detect payment completion
/// 3. Handles success/failure callbacks
/// 4. Navigates to appropriate screens based on payment status
class PaymentGatewayScreen extends StatefulWidget {
  const PaymentGatewayScreen({
    super.key,
    required this.paymentUrl,
    required this.callbackUrl,
    required this.paymentId,
    required this.onPaymentComplete,
  });
  final String paymentUrl;
  final String callbackUrl;
  final String paymentId;
  final Function(Map<String, dynamic>) onPaymentComplete;

  @override
  State<PaymentGatewayScreen> createState() => _PaymentGatewayScreenState();
}

class _PaymentGatewayScreenState extends State<PaymentGatewayScreen> {
  late final WebViewController _controller;
  bool _isLoading = true;
  bool _hasError = false;
  String _errorMessage = '';

  @override
  void initState() {
    super.initState();
    _initializeWebView();
  }

  void _initializeWebView() {
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(Colors.white)
      ..setNavigationDelegate(
        NavigationDelegate(
          onProgress: (int progress) {
            setState(() {
              _isLoading = progress < 100;
            });
          },
          onPageStarted: (String url) {
            debugPrint('Payment page started: $url');
            setState(() {
              _isLoading = true;
              _hasError = false;
            });
          },
          onPageFinished: (String url) {
            debugPrint('Payment page finished: $url');
            setState(() {
              _isLoading = false;
            });

            // Check if this is a callback URL
            if (url.startsWith(widget.callbackUrl)) {
              _handleCallback(url);
            }
          },
          onHttpError: (HttpResponseError error) {
            debugPrint('HTTP error: ${error.response?.statusCode}');
            setState(() {
              _hasError = true;
              _errorMessage = 'Failed to load payment page. Please try again.';
              _isLoading = false;
            });
          },
          onWebResourceError: (WebResourceError error) {
            debugPrint('Web resource error: ${error.description}');
            setState(() {
              _hasError = true;
              _errorMessage = error.description;
              _isLoading = false;
            });
          },
          onNavigationRequest: (NavigationRequest request) {
            debugPrint('Navigation request: ${request.url}');

            // Intercept callback URLs
            if (request.url.startsWith(widget.callbackUrl)) {
              _handleCallback(request.url);
              return NavigationDecision.prevent;
            }

            return NavigationDecision.navigate;
          },
        ),
      )
      ..loadRequest(Uri.parse(widget.paymentUrl));
  }

  void _handleCallback(String url) {
    debugPrint('Handling payment callback: $url');

    final uri = Uri.parse(url);
    final params = uri.queryParameters;

    // Extract payment status and details from URL parameters
    // Khalti format: ?pidx=xxx&status=Completed&transaction_id=xxx&amount=1000&...
    final status = params['status'] ?? 'Unknown';
    final transactionId = params['transaction_id'] ?? params['txnId'] ?? '';
    final amount = params['amount'] ?? params['total_amount'] ?? '';
    final pidx = params['pidx'] ?? '';

    debugPrint('Payment status: $status');
    debugPrint('Transaction ID: $transactionId');
    debugPrint('Amount: $amount');

    // Create callback result
    final result = {
      'status': status,
      'transaction_id': transactionId,
      'amount': amount,
      'pidx': pidx,
      'payment_id': widget.paymentId,
      'raw_params': params,
    };

    // Call completion callback
    widget.onPaymentComplete(result);

    // Navigate back or to appropriate screen based on status
    if (status == 'Completed') {
      _showSuccessDialog(result);
    } else if (status == 'User canceled' || status == 'Expired') {
      _showFailureDialog(status);
    } else if (status == 'Pending') {
      _showPendingDialog();
    } else {
      _showErrorDialog('Unknown payment status: $status');
    }
  }

  void _showSuccessDialog(Map<String, dynamic> result) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.check_circle, color: Colors.green, size: 32),
            SizedBox(width: 12),
            Text('Payment Successful'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Your payment has been completed successfully!'),
            const SizedBox(height: 16),
            const Text('Transaction ID:',
                style: TextStyle(fontWeight: FontWeight.bold)),
            Text(result['transaction_id'] ?? 'N/A'),
            const SizedBox(height: 8),
            const Text('Amount:',
                style: TextStyle(fontWeight: FontWeight.bold)),
            Text('Rs. ${(int.tryParse(result['amount'] ?? '0') ?? 0) / 100}'),
          ],
        ),
        actions: [
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop(); // Close dialog
              Navigator.of(context)
                  .pop(result); // Return to previous screen with result
            },
            child: const Text('View Receipt'),
          ),
        ],
      ),
    );
  }

  void _showFailureDialog(String status) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.error, color: Colors.red, size: 32),
            SizedBox(width: 12),
            Text('Payment Failed'),
          ],
        ),
        content: Text('Payment was $status. Please try again.'),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop(); // Close dialog
              Navigator.of(context).pop({
                'status': 'failed',
                'reason': status
              }); // Return to previous screen
            },
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  void _showPendingDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.info, color: Colors.orange, size: 32),
            SizedBox(width: 12),
            Text('Payment Pending'),
          ],
        ),
        content: const Text(
            'Your payment is being processed. We will notify you once it\'s confirmed. '
            'If not updated within 24 hours, please contact support.'),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop(); // Close dialog
              Navigator.of(context)
                  .pop({'status': 'pending'}); // Return to previous screen
            },
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  void _showErrorDialog(String message) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning, color: Colors.orange, size: 32),
            SizedBox(width: 12),
            Text('Error'),
          ],
        ),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop(); // Close dialog
              Navigator.of(context).pop({
                'status': 'error',
                'message': message
              }); // Return to previous screen
            },
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('Complete Payment'),
          leading: IconButton(
            icon: const Icon(Icons.close),
            onPressed: () {
              // Show confirmation dialog before closing
              showDialog(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('Cancel Payment?'),
                  content: const Text(
                      'Are you sure you want to cancel this payment?'),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text('No'),
                    ),
                    ElevatedButton(
                      onPressed: () {
                        Navigator.of(context).pop(); // Close dialog
                        Navigator.of(context).pop({
                          'status': 'canceled'
                        }); // Return to previous screen
                      },
                      style:
                          ElevatedButton.styleFrom(backgroundColor: Colors.red),
                      child: const Text('Yes, Cancel'),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
        body: Stack(
          children: [
            if (!_hasError)
              WebViewWidget(controller: _controller)
            else
              Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.error_outline,
                        size: 64, color: Colors.red),
                    const SizedBox(height: 16),
                    const Text(
                      'Failed to Load Payment Page',
                      style:
                          TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 32),
                      child: Text(
                        _errorMessage,
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.grey[600]),
                      ),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: () {
                        setState(() {
                          _hasError = false;
                          _errorMessage = '';
                        });
                        _controller.loadRequest(Uri.parse(widget.paymentUrl));
                      },
                      icon: const Icon(Icons.refresh),
                      label: const Text('Retry'),
                    ),
                  ],
                ),
              ),

            // Loading indicator
            if (_isLoading && !_hasError)
              Container(
                color: Colors.white,
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const CircularProgressIndicator(),
                      const SizedBox(height: 16),
                      const Text(
                        'Loading payment page...',
                        style: TextStyle(fontSize: 16),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Please wait',
                        style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      );

  @override
  void dispose() {
    // Webview cleanup is handled automatically
    super.dispose();
  }
}
