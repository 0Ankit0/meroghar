import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:webview_flutter/webview_flutter.dart';
import '../../data/models/payment.dart';
import '../providers/payment_provider.dart';

class PaymentResult {
  final bool success;
  final String message;
  final VerifyPaymentResponse? response;

  const PaymentResult(
      {required this.success, required this.message, this.response});
}

class PaymentWebViewPage extends ConsumerStatefulWidget {
  final PaymentProvider provider;
  final String? paymentUrl;
  final String? esewaFormAction;
  final Map<String, dynamic>? esewaFormFields;
  final String callbackUrlPrefix;

  const PaymentWebViewPage({
    super.key,
    required this.provider,
    this.paymentUrl,
    this.esewaFormAction,
    this.esewaFormFields,
    this.callbackUrlPrefix = 'http://localhost:3000/payment-callback',
  });

  @override
  ConsumerState<PaymentWebViewPage> createState() => _PaymentWebViewPageState();
}

class _PaymentWebViewPageState extends ConsumerState<PaymentWebViewPage> {
  late final WebViewController _controller;
  bool _loading = true;
  bool _verifying = false;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (_) => setState(() => _loading = true),
          onPageFinished: (_) => setState(() => _loading = false),
          onNavigationRequest: _onNavRequest,
        ),
      );

    if (widget.provider == PaymentProvider.esewa) {
      _loadEsewaForm();
      return;
    }

    final paymentUrl = widget.paymentUrl;
    if (paymentUrl == null || paymentUrl.trim().isEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        Navigator.of(context).pop(
          const PaymentResult(
            success: false,
            message: 'Payment URL is unavailable for this checkout.',
          ),
        );
      });
      return;
    }

    _controller.loadRequest(Uri.parse(paymentUrl));
  }

  void _loadEsewaForm() {
    final action = widget.esewaFormAction ??
        'https://rc-epay.esewa.com.np/api/epay/main/v2/form';
    final fields = widget.esewaFormFields ?? {};
    final inputs = fields.entries
        .map(
          (entry) =>
              '<input type="hidden" name="${entry.key}" value="${entry.value}" />',
        )
        .join('\n');

    final html = '''
<!DOCTYPE html>
<html>
<body>
  <p style="font-family:sans-serif;text-align:center;margin-top:40px">
    Redirecting to eSewa…
  </p>
  <form id="f" method="POST" action="$action">
    $inputs
  </form>
  <script>document.getElementById('f').submit();</script>
</body>
</html>''';

    _controller.loadHtmlString(html);
  }

  NavigationDecision _onNavRequest(NavigationRequest request) {
    final url = request.url;
    if (url.startsWith(widget.callbackUrlPrefix)) {
      _handleCallback(Uri.parse(url));
      return NavigationDecision.prevent;
    }
    return NavigationDecision.navigate;
  }

  Future<void> _handleCallback(Uri uri) async {
    if (_verifying) return;
    setState(() => _verifying = true);

    final repo = ref.read(paymentRepositoryProvider);

    try {
      final verifyRequest = _buildVerifyRequest(uri);
      final result = await repo.verifyPayment(verifyRequest);
      if (!mounted) return;
      Navigator.of(context).pop(
        PaymentResult(
          success: result.status == PaymentStatus.completed,
          message: result.status == PaymentStatus.completed
              ? 'Payment completed successfully!'
              : 'Payment status: ${result.status.name}',
          response: result,
        ),
      );
    } catch (error) {
      if (!mounted) return;
      Navigator.of(context).pop(
        PaymentResult(success: false, message: error.toString()),
      );
    }
  }

  VerifyPaymentRequest _buildVerifyRequest(Uri uri) {
    switch (widget.provider) {
      case PaymentProvider.khalti:
        return VerifyPaymentRequest(
          provider: PaymentProvider.khalti,
          pidx: uri.queryParameters['pidx'],
        );
      case PaymentProvider.esewa:
        return VerifyPaymentRequest(
          provider: PaymentProvider.esewa,
          data: uri.queryParameters['data'],
        );
      case PaymentProvider.stripe:
        return VerifyPaymentRequest(
          provider: PaymentProvider.stripe,
          pidx: uri.queryParameters['session_id'],
        );
      case PaymentProvider.paypal:
        return VerifyPaymentRequest(
          provider: PaymentProvider.paypal,
          pidx: uri.queryParameters['paymentId'],
          oid: uri.queryParameters['PayerID'],
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.provider.displayName} checkout'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(
            const PaymentResult(success: false, message: 'Payment cancelled'),
          ),
        ),
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_loading || _verifying)
            Container(
              color: Colors.white.withValues(alpha: 0.85),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const CircularProgressIndicator(),
                    const SizedBox(height: 16),
                    Text(
                      _verifying ? 'Verifying payment…' : 'Loading…',
                      style: const TextStyle(fontSize: 14),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
