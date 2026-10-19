import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';
import '../models/customer_profile.dart';
import '../models/profile_input.dart';

class ProfileRepository {
  ProfileRepository(this._api);

  final ApiClient _api;

  Future<CustomerProfile> fetch() async {
    final response = await _api.send((dio) => dio.get<Map<String, dynamic>>(ApiEndpoints.customerProfile));
    return CustomerProfile.fromJson(response.data!);
  }

  Future<CustomerProfile> update(ProfileInput input) async {
    final response = await _api.send((dio) => dio.patch<Map<String, dynamic>>(
          ApiEndpoints.customerProfile,
          data: input.toJson(),
        ));
    return CustomerProfile.fromJson(response.data!);
  }
}
