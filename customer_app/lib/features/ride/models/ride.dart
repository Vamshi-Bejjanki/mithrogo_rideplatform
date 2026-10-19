import '../../../core/utils/json.dart';
import 'ride_options.dart';

/// Matches apps.rides.RideStatus in the backend.
enum RideStatus {
  requested('REQUESTED'),
  searching('SEARCHING'),
  accepted('ACCEPTED'),
  captainArrived('CAPTAIN_ARRIVED'),
  started('STARTED'),
  completed('COMPLETED'),
  cancelled('CANCELLED'),
  unknown('');

  const RideStatus(this.apiValue);

  final String apiValue;

  static RideStatus fromApi(String value) {
    return RideStatus.values.firstWhere(
      (status) => status.apiValue == value,
      orElse: () => RideStatus.unknown,
    );
  }

  bool get isSearching => this == requested || this == searching;

  bool get isTerminal => this == completed || this == cancelled;

  /// The customer can still cancel until the trip starts.
  bool get canCancel => isSearching || this == accepted || this == captainArrived;
}

/// Matches RideSerializer in the backend.
class Ride {
  const Ride({
    required this.id,
    required this.status,
    required this.vehicleType,
    required this.pickupAddress,
    required this.dropAddress,
    required this.estimatedFare,
    required this.paymentMethod,
    this.paymentStatus = '',
    this.finalFare,
    this.estimatedDistanceKm,
    this.estimatedDurationMinutes,
    this.requestedAt,
    this.captainName,
    this.captainRating,
    this.cancellationReason,
  });

  factory Ride.fromJson(Map<String, dynamic> json) {
    final captain = json['captain'] as Map<String, dynamic>?;
    return Ride(
      id: json['id'] as String,
      status: RideStatus.fromApi(json['status'] as String? ?? ''),
      vehicleType: VehicleType.fromApi(json['vehicle_type'] as String? ?? ''),
      pickupAddress: json['pickup_address'] as String? ?? '',
      dropAddress: json['drop_address'] as String? ?? '',
      estimatedFare: json['estimated_fare']?.toString() ?? '0.00',
      finalFare: json['final_fare']?.toString(),
      estimatedDistanceKm: parseDoubleOrNull(json['estimated_distance_km']),
      estimatedDurationMinutes: (json['estimated_duration_minutes'] as num?)?.toInt(),
      paymentMethod: json['payment_method'] as String? ?? PaymentMethod.cash.apiValue,
      paymentStatus: json['payment_status'] as String? ?? '',
      requestedAt: DateTime.tryParse(json['requested_at'] as String? ?? '')?.toLocal(),
      captainName: captain?['name'] as String?,
      captainRating: parseDoubleOrNull(captain?['rating']),
      cancellationReason: json['cancellation_reason'] as String?,
    );
  }

  final String id;
  final RideStatus status;
  final VehicleType vehicleType;
  final String pickupAddress;
  final String dropAddress;

  /// Money as the backend sends it: a string with two decimals.
  final String estimatedFare;
  final String? finalFare;
  final double? estimatedDistanceKm;
  final int? estimatedDurationMinutes;
  final String paymentMethod;

  /// The backend's RidePaymentStatus: UNPAID or PAID.
  final String paymentStatus;
  final DateTime? requestedAt;
  final String? captainName;
  final double? captainRating;
  final String? cancellationReason;

  /// Final fare once the ride is done, otherwise the estimate.
  String get displayFare => finalFare ?? estimatedFare;

  bool get isOnline => paymentMethod == PaymentMethod.online.apiValue;

  bool get isPaid => paymentStatus == 'PAID';

  /// A completed online ride still waiting for the customer to pay.
  bool get needsOnlinePayment => status == RideStatus.completed && isOnline && !isPaid;
}

/// Matches services.estimate() in the backend.
class FareEstimate {
  const FareEstimate({
    required this.vehicleType,
    required this.distanceKm,
    required this.durationMinutes,
    required this.fare,
  });

  factory FareEstimate.fromJson(Map<String, dynamic> json) {
    return FareEstimate(
      vehicleType: VehicleType.fromApi(json['vehicle_type'] as String? ?? ''),
      distanceKm: parseDouble(json['distance_km']),
      durationMinutes: (json['duration_minutes'] as num?)?.toInt() ?? 0,
      fare: json['fare']?.toString() ?? '0.00',
    );
  }

  final VehicleType vehicleType;
  final double distanceKm;
  final int durationMinutes;
  final String fare;
}
