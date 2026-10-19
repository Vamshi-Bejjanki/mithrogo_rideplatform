/// Matches NotificationSerializer in the backend.
class AppNotification {
  const AppNotification({
    required this.id,
    required this.type,
    required this.title,
    required this.message,
    required this.isRead,
    this.createdAt,
    this.data = const {},
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: (json['id'] as num).toInt(),
      type: json['type'] as String? ?? '',
      title: json['title'] as String? ?? '',
      message: json['message'] as String? ?? '',
      isRead: json['is_read'] as bool? ?? false,
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? '')?.toLocal(),
      data: (json['data'] as Map?)?.cast<String, dynamic>() ?? const {},
    );
  }

  final int id;
  final String type;
  final String title;
  final String message;
  final bool isRead;
  final DateTime? createdAt;
  final Map<String, dynamic> data;

  /// The ride this notification is about, when the backend attached one.
  String? get rideId => data['ride_id']?.toString();

  AppNotification markedRead() => AppNotification(
        id: id,
        type: type,
        title: title,
        message: message,
        isRead: true,
        createdAt: createdAt,
        data: data,
      );
}
