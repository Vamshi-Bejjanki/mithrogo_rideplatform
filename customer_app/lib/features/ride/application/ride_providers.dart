import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/providers.dart';
import '../../../core/network/api_exception.dart';
import '../data/ride_repository.dart';
import '../models/ride.dart';
import '../models/ride_tracking.dart';

/// Polls tracking every few seconds until the ride reaches a final status.
/// Cancelling the subscription (leaving the screen) stops the polling.
final rideTrackingProvider = StreamProvider.autoDispose.family<RideTracking, String>((ref, rideId) {
  final repository = ref.watch(rideRepositoryProvider);
  return _pollTracking(repository, rideId);
});

Stream<RideTracking> _pollTracking(RideRepository repository, String rideId) async* {
  var hasData = false;
  while (true) {
    try {
      final tracking = await repository.tracking(rideId);
      hasData = true;
      yield tracking;
      if (tracking.status.isTerminal) return;
    } on ApiException catch (error) {
      // Before the first result, show the error. After it, a dropped connection keeps the
      // last known state on screen and polling carries on, instead of freezing the ride.
      if (!hasData || !error.isNetworkError) rethrow;
    }
    await Future<void>.delayed(const Duration(seconds: 4));
  }
}

final rideDetailProvider = FutureProvider.autoDispose.family<Ride, String>((ref, rideId) {
  return ref.watch(rideRepositoryProvider).fetch(rideId);
});

final rideHistoryProvider = FutureProvider.autoDispose<List<Ride>>((ref) {
  return ref.watch(rideRepositoryProvider).history();
});

/// The customer's ride that is still in progress, if any. The backend allows only one at a time,
/// so the newest non-final ride in the history is the one to resume.
final activeRideProvider = FutureProvider.autoDispose<Ride?>((ref) async {
  final rides = await ref.watch(rideHistoryProvider.future);
  for (final ride in rides) {
    if (!ride.status.isTerminal && ride.status != RideStatus.unknown) return ride;
  }
  return null;
});
