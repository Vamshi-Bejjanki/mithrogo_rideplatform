import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';
import '../models/app_notification.dart';

class NotificationRepository {
  NotificationRepository(this._api);

  final ApiClient _api;

  Future<List<AppNotification>> list() async {
    final response = await _api.send((dio) => dio.get<List<dynamic>>(ApiEndpoints.notifications));
    return (response.data ?? const <dynamic>[])
        .map((item) => AppNotification.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<AppNotification> markRead(int id) async {
    final response = await _api.send(
      (dio) => dio.post<Map<String, dynamic>>(ApiEndpoints.notificationRead(id)),
    );
    return AppNotification.fromJson(response.data!);
  }
}
