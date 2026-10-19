import 'lat_lng.dart';

/// Where the rider is. Swap [MockLocationService] for a GPS-backed
/// implementation later without touching the screens.
abstract class LocationService {
  Future<LatLng> currentLocation();
}

class MockLocationService implements LocationService {
  static const demoLocation = LatLng(latitude: 18.6725, longitude: 73.8567);

  @override
  Future<LatLng> currentLocation() async {
    await Future<void>.delayed(const Duration(milliseconds: 300));
    return demoLocation;
  }
}
