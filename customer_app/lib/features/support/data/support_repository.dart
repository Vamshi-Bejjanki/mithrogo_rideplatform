import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';
import '../models/support_ticket.dart';

class SupportRepository {
  SupportRepository(this._api);

  final ApiClient _api;

  Future<List<SupportTicket>> list() async {
    final response = await _api.send((dio) => dio.get<List<dynamic>>(ApiEndpoints.supportTickets));
    return (response.data ?? const <dynamic>[])
        .map((item) => SupportTicket.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<SupportTicket> create({
    required TicketCategory category,
    required String description,
    String? rideId,
  }) async {
    final response = await _api.send((dio) => dio.post<Map<String, dynamic>>(
          ApiEndpoints.supportTickets,
          data: {
            'category': category.apiValue,
            'description': description,
            'ride_id': ?rideId,
          },
        ));
    return SupportTicket.fromJson(response.data!);
  }
}
