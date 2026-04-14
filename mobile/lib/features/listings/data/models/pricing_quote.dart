import 'package:equatable/equatable.dart';
import 'listing_parsing.dart';
import 'listing_search.dart';

class PricingLineItem extends Equatable {
  final String label;
  final double amount;
  final String? description;

  const PricingLineItem({
    required this.label,
    required this.amount,
    this.description,
  });

  factory PricingLineItem.fromJson(Map<String, dynamic> json) {
    return PricingLineItem(
      label: readString(json, ['label', 'name', 'title', 'type']) ?? 'Charge',
      amount: readDouble(json, ['amount', 'value', 'total']) ?? 0,
      description: readString(json, ['description', 'detail']),
    );
  }

  @override
  List<Object?> get props => [label, amount, description];
}

class PricingQuote extends Equatable {
  final String propertyId;
  final ListingDateRange period;
  final String currency;
  final String? rateLabel;
  final double baseFee;
  final double peakSurcharge;
  final double serviceFee;
  final double taxAmount;
  final double depositAmount;
  final double totalFee;
  final double totalDueNow;
  final bool? isAvailable;
  final String? note;
  final List<PricingLineItem> lineItems;

  const PricingQuote({
    required this.propertyId,
    required this.period,
    required this.currency,
    required this.baseFee,
    required this.peakSurcharge,
    required this.serviceFee,
    required this.taxAmount,
    required this.depositAmount,
    required this.totalFee,
    required this.totalDueNow,
    this.rateLabel,
    this.isAvailable,
    this.note,
    this.lineItems = const [],
  });

  static double _subtotal(
    double baseFee,
    double peakSurcharge,
    double serviceFee,
    double taxAmount,
  ) {
    return baseFee + peakSurcharge + serviceFee + taxAmount;
  }

  static List<PricingLineItem> _defaultItems({
    required double baseFee,
    required double peakSurcharge,
    required double serviceFee,
    required double taxAmount,
    required double depositAmount,
  }) {
    final items = <PricingLineItem>[];
    if (baseFee != 0) {
      items.add(PricingLineItem(label: 'Base rent', amount: baseFee));
    }
    if (peakSurcharge != 0) {
      items
          .add(PricingLineItem(label: 'Peak surcharge', amount: peakSurcharge));
    }
    if (serviceFee != 0) {
      items.add(PricingLineItem(label: 'Service fee', amount: serviceFee));
    }
    if (taxAmount != 0) {
      items.add(PricingLineItem(label: 'Tax', amount: taxAmount));
    }
    if (depositAmount != 0) {
      items.add(
          PricingLineItem(label: 'Security deposit', amount: depositAmount));
    }
    return items;
  }

  factory PricingQuote.fromJson(
    Map<String, dynamic> json, {
    required ListingDateRange requestedPeriod,
  }) {
    final pricing = readMap(json, ['pricing']);
    final source = pricing.isNotEmpty ? pricing : json;
    final baseFee = readDouble(source,
            ['base_fee', 'base', 'monthly_rent', 'base_rental_fee', 'rent']) ??
        0;
    final peakSurcharge =
        readDouble(source, ['peak_surcharge', 'seasonal_surcharge']) ?? 0;
    final serviceFee = readDouble(source, ['service_fee']) ?? 0;
    final taxAmount = readDouble(source, ['tax_amount', 'tax']) ?? 0;
    final depositAmount =
        readDouble(source, ['deposit_amount', 'security_deposit', 'deposit']) ??
            0;
    final totalFee = readDouble(
          source,
          ['total_fee', 'quote_total', 'total', 'subtotal'],
        ) ??
        _subtotal(baseFee, peakSurcharge, serviceFee, taxAmount);
    final totalDueNow =
        readDouble(source, ['total_due_now', 'due_now', 'payable_now']) ??
            totalFee;
    final rawLineItems = readList(source, ['line_items', 'breakdown', 'items']);
    final lineItems = rawLineItems
        .map((item) => PricingLineItem.fromJson(asJsonMap(item)))
        .where((item) => item.amount != 0)
        .toList();

    return PricingQuote(
      propertyId: readString(source, ['property_id', 'id']) ??
          readString(json, ['property_id', 'id']) ??
          '',
      period: requestedPeriod,
      currency: readString(source, ['currency']) ??
          readString(json, ['currency']) ??
          'NPR',
      rateLabel:
          readString(source, ['rate_label', 'tier', 'pricing_tier', 'summary']),
      baseFee: baseFee,
      peakSurcharge: peakSurcharge,
      serviceFee: serviceFee,
      taxAmount: taxAmount,
      depositAmount: depositAmount,
      totalFee: totalFee,
      totalDueNow: totalDueNow,
      isAvailable: readBool(source, ['available', 'is_available']),
      note: readString(source, ['message', 'note']),
      lineItems: lineItems.isNotEmpty
          ? lineItems
          : _defaultItems(
              baseFee: baseFee,
              peakSurcharge: peakSurcharge,
              serviceFee: serviceFee,
              taxAmount: taxAmount,
              depositAmount: depositAmount,
            ),
    );
  }

  @override
  List<Object?> get props => [
        propertyId,
        period,
        currency,
        rateLabel,
        baseFee,
        peakSurcharge,
        serviceFee,
        taxAmount,
        depositAmount,
        totalFee,
        totalDueNow,
        isAvailable,
        note,
        lineItems,
      ];
}
