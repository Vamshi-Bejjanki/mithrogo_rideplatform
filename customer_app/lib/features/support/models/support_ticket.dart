/// Matches apps.support.TicketCategory in the backend.
enum TicketCategory {
  rideIssue('RIDE_ISSUE', 'Issue with a ride'),
  payment('PAYMENT', 'Payment or fare'),
  safety('SAFETY', 'Safety'),
  account('ACCOUNT', 'Account'),
  other('OTHER', 'Other');

  const TicketCategory(this.apiValue, this.label);

  final String apiValue;
  final String label;

  static TicketCategory fromApi(String value) {
    return TicketCategory.values.firstWhere(
      (category) => category.apiValue == value,
      orElse: () => TicketCategory.other,
    );
  }
}

/// Matches TicketSerializer in the backend.
class SupportTicket {
  const SupportTicket({
    required this.id,
    required this.category,
    required this.description,
    required this.status,
    this.rideId,
    this.resolutionNote = '',
    this.createdAt,
  });

  factory SupportTicket.fromJson(Map<String, dynamic> json) {
    return SupportTicket(
      id: (json['id'] as num).toInt(),
      category: TicketCategory.fromApi(json['category'] as String? ?? ''),
      description: json['description'] as String? ?? '',
      status: json['status'] as String? ?? 'OPEN',
      rideId: json['ride_id']?.toString(),
      resolutionNote: json['resolution_note'] as String? ?? '',
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? '')?.toLocal(),
    );
  }

  final int id;
  final TicketCategory category;
  final String description;

  /// OPEN, IN_PROGRESS, RESOLVED or CLOSED.
  final String status;
  final String? rideId;
  final String resolutionNote;
  final DateTime? createdAt;

  bool get isOpen => status == 'OPEN' || status == 'IN_PROGRESS';

  String get statusLabel => switch (status) {
        'OPEN' => 'Open',
        'IN_PROGRESS' => 'In progress',
        'RESOLVED' => 'Resolved',
        'CLOSED' => 'Closed',
        _ => status,
      };
}
