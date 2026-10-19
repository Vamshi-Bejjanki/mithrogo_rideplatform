import 'package:customer_app/features/support/models/support_ticket.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('SupportTicket.fromJson reads the TicketSerializer shape', () {
    final ticket = SupportTicket.fromJson({
      'id': 3,
      'category': 'SAFETY',
      'description': 'Driver was rude',
      'ride_id': 'r-9',
      'status': 'IN_PROGRESS',
      'resolution_note': '',
      'created_at': '2026-10-15T09:05:00Z',
    });

    expect(ticket.category, TicketCategory.safety);
    expect(ticket.rideId, 'r-9');
    expect(ticket.isOpen, isTrue);
    expect(ticket.statusLabel, 'In progress');
  });

  test('resolved tickets are not open and unknown categories fall back to other', () {
    final ticket = SupportTicket.fromJson({'id': 1, 'category': 'NEW_THING', 'status': 'RESOLVED'});
    expect(ticket.category, TicketCategory.other);
    expect(ticket.isOpen, isFalse);
    expect(ticket.rideId, isNull);
  });
}
