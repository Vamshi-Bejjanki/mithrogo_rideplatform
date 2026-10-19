/// A pickup or drop point. [address] is what the backend stores on the ride.
class Place {
  const Place({
    required this.name,
    required this.address,
    required this.latitude,
    required this.longitude,
  });

  final String name;
  final String address;
  final double latitude;
  final double longitude;
}
