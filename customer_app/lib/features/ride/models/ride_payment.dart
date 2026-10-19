/// Matches PaymentSerializer in the backend.
class RidePayment {
  const RidePayment({
    required this.id,
    required this.amount,
    required this.status,
    required this.providerOrderId,
  });

  factory RidePayment.fromJson(Map<String, dynamic> json) {
    return RidePayment(
      id: json['id'] as String,
      amount: json['amount']?.toString() ?? '0.00',
      status: json['status'] as String? ?? '',
      providerOrderId: json['provider_order_id'] as String? ?? '',
    );
  }

  final String id;
  final String amount;

  /// CREATED, PENDING, PAID or FAILED.
  final String status;
  final String providerOrderId;

  bool get isPaid => status == 'PAID';

  bool get isFailed => status == 'FAILED';
}
