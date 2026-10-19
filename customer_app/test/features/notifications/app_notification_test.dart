import 'package:customer_app/features/notifications/models/app_notification.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('AppNotification.fromJson reads the NotificationSerializer shape', () {
    final notification = AppNotification.fromJson({
      'id': 7,
      'type': 'RIDE_ACCEPTED',
      'title': 'Captain accepted',
      'message': 'Your captain is on the way.',
      'data': {'ride_id': 'r-1'},
      'is_read': false,
      'created_at': '2026-10-15T09:05:00Z',
    });

    expect(notification.id, 7);
    expect(notification.rideId, 'r-1');
    expect(notification.isRead, isFalse);
    expect(notification.markedRead().isRead, isTrue);
    expect(notification.createdAt, isNotNull);
  });

  test('a notification without ride data has no ride id', () {
    final notification = AppNotification.fromJson({'id': 1, 'type': 'X', 'title': 'T', 'data': {}});
    expect(notification.rideId, isNull);
    expect(notification.message, '');
  });
}
