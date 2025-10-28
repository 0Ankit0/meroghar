import 'package:flutter/material.dart';

/// Payment method selection screen.
///
/// Implements T120 from tasks.md.
///
/// Allows tenant to choose between:
/// - Khalti (primary gateway)
/// - eSewa (backup gateway)
/// - IME Pay (backup gateway)
class PaymentMethodScreen extends StatefulWidget {
  const PaymentMethodScreen({
    Key? key,
    required this.amount,
    required this.tenantId,
    required this.paymentType,
  }) : super(key: key);
  final double amount;
  final String tenantId;
  final String paymentType;

  @override
  State<PaymentMethodScreen> createState() => _PaymentMethodScreenState();
}

class _PaymentMethodScreenState extends State<PaymentMethodScreen> {
  String? _selectedMethod;
  bool _isProcessing = false;

  final List<PaymentMethodOption> _paymentMethods = [
    PaymentMethodOption(
      id: 'KHALTI',
      name: 'Khalti',
      description: 'Pay with Khalti digital wallet',
      logoAsset: 'assets/images/khalti_logo.png',
      isAvailable: true,
      isRecommended: true,
    ),
    PaymentMethodOption(
      id: 'ESEWA',
      name: 'eSewa',
      description: 'Pay with eSewa digital wallet',
      logoAsset: 'assets/images/esewa_logo.png',
      isAvailable: false, // Will be available when T111 is implemented
      isRecommended: false,
    ),
    PaymentMethodOption(
      id: 'IMEPAY',
      name: 'IME Pay',
      description: 'Pay with IME Pay',
      logoAsset: 'assets/images/imepay_logo.png',
      isAvailable: false, // Will be available when T112 is implemented
      isRecommended: false,
    ),
  ];

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: Text('Select Payment Method'),
          centerTitle: true,
        ),
        body: Column(
          children: [
            // Amount display
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Theme.of(context).primaryColor.withOpacity(0.1),
                border: Border(
                  bottom: BorderSide(
                    color: Colors.grey[300]!,
                    width: 1,
                  ),
                ),
              ),
              child: Column(
                children: [
                  Text(
                    'Amount to Pay',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey[600],
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Rs. ${widget.amount.toStringAsFixed(2)}',
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: Theme.of(context).primaryColor,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    widget.paymentType,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[500],
                    ),
                  ),
                ],
              ),
            ),

            // Payment methods list
            Expanded(
              child: ListView.builder(
                padding: EdgeInsets.all(16),
                itemCount: _paymentMethods.length,
                itemBuilder: (context, index) {
                  final method = _paymentMethods[index];
                  return _buildPaymentMethodCard(method);
                },
              ),
            ),

            // Proceed button
            Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black12,
                    offset: Offset(0, -2),
                    blurRadius: 4,
                  ),
                ],
              ),
              child: SafeArea(
                child: SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _selectedMethod != null && !_isProcessing
                        ? _proceedToPayment
                        : null,
                    child: _isProcessing
                        ? SizedBox(
                            height: 24,
                            width: 24,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor:
                                  AlwaysStoppedAnimation<Color>(Colors.white),
                            ),
                          )
                        : Text(
                            'Proceed to Payment',
                            style: TextStyle(
                                fontSize: 16, fontWeight: FontWeight.bold),
                          ),
                  ),
                ),
              ),
            ),
          ],
        ),
      );

  Widget _buildPaymentMethodCard(PaymentMethodOption method) {
    final isSelected = _selectedMethod == method.id;
    final canSelect = method.isAvailable && !_isProcessing;

    return Card(
      margin: EdgeInsets.only(bottom: 12),
      elevation: isSelected ? 4 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color:
              isSelected ? Theme.of(context).primaryColor : Colors.grey[300]!,
          width: isSelected ? 2 : 1,
        ),
      ),
      child: InkWell(
        onTap: canSelect
            ? () {
                setState(() {
                  _selectedMethod = method.id;
                });
              }
            : null,
        borderRadius: BorderRadius.circular(12),
        child: Opacity(
          opacity: method.isAvailable ? 1.0 : 0.5,
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Row(
              children: [
                // Radio button
                Radio<String>(
                  value: method.id,
                  groupValue: _selectedMethod,
                  onChanged: canSelect
                      ? (value) {
                          setState(() {
                            _selectedMethod = value;
                          });
                        }
                      : null,
                ),
                SizedBox(width: 12),

                // Logo placeholder (will be replaced with actual logo when assets are added)
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: Colors.grey[200],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.payment, color: Colors.grey[600]),
                ),
                SizedBox(width: 16),

                // Method details
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            method.name,
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          if (method.isRecommended) ...[
                            SizedBox(width: 8),
                            Container(
                              padding: EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 2,
                              ),
                              decoration: BoxDecoration(
                                color: Colors.green,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                'RECOMMENDED',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                      SizedBox(height: 4),
                      Text(
                        method.description,
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey[600],
                        ),
                      ),
                      if (!method.isAvailable) ...[
                        SizedBox(height: 4),
                        Text(
                          'Coming soon',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.orange,
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),

                // Checkmark for selected
                if (isSelected)
                  Icon(
                    Icons.check_circle,
                    color: Theme.of(context).primaryColor,
                    size: 28,
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _proceedToPayment() async {
    if (_selectedMethod == null) return;

    setState(() {
      _isProcessing = true;
    });

    try {
      // Return selected method to previous screen
      // The calling screen will handle API call to initiate payment
      Navigator.of(context).pop({
        'payment_method': _selectedMethod,
        'amount': widget.amount,
      });
    } catch (e) {
      setState(() {
        _isProcessing = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to process payment: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}

/// Payment method option model
class PaymentMethodOption {
  PaymentMethodOption({
    required this.id,
    required this.name,
    required this.description,
    required this.logoAsset,
    required this.isAvailable,
    required this.isRecommended,
  });
  final String id;
  final String name;
  final String description;
  final String logoAsset;
  final bool isAvailable;
  final bool isRecommended;
}
