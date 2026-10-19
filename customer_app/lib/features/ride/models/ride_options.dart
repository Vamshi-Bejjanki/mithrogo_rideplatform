/// Matches apps.vehicles.VehicleType in the backend.
enum VehicleType {
  bike('BIKE', 'Bike'),
  auto('AUTO', 'Auto');

  const VehicleType(this.apiValue, this.label);

  final String apiValue;
  final String label;

  static VehicleType fromApi(String value) {
    return VehicleType.values.firstWhere(
      (type) => type.apiValue == value,
      orElse: () => VehicleType.bike,
    );
  }
}

/// Matches apps.rides.PaymentMethod in the backend.
enum PaymentMethod {
  cash('CASH', 'Cash'),
  online('ONLINE', 'UPI / Card');

  const PaymentMethod(this.apiValue, this.label);

  final String apiValue;
  final String label;
}
