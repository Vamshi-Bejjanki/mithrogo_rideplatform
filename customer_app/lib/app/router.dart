import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/application/session_controller.dart';
import '../features/auth/presentation/login_screen.dart';
import '../features/auth/presentation/otp_screen.dart';
import '../features/auth/presentation/signup_screen.dart';
import '../features/booking/presentation/location_search_screen.dart';
import '../features/emergency/presentation/emergency_screen.dart';
import '../features/history/presentation/history_screen.dart';
import '../features/home/presentation/home_screen.dart';
import '../features/notifications/presentation/notifications_screen.dart';
import '../features/profile/presentation/edit_profile_screen.dart';
import '../features/profile/presentation/profile_screen.dart';
import '../features/ride/presentation/ride_screen.dart';
import '../features/settings/presentation/settings_screen.dart';
import '../features/splash/presentation/splash_screen.dart';
import '../features/support/presentation/support_screen.dart';
import 'app_shell.dart';

abstract final class AppRoutes {
  static const splash = '/splash';
  static const login = '/login';
  static const otp = '/otp';
  static const profileSetup = '/profile-setup';
  static const home = '/home';
  static const history = '/history';
  static const profile = '/profile';
  static const search = '/search';
  static const editProfile = '/edit-profile';
  static const settings = '/settings';
  static const notifications = '/notifications';
  static const support = '/support';
  static const emergency = '/emergency';

  /// Live ride screen for one ride, e.g. /ride/3f2a...
  static String rideDetail(String rideId) => '/ride/$rideId';
}

final routerProvider = Provider<GoRouter>((ref) {
  // GoRouter re-runs `redirect` whenever this notifies, so auth changes take effect at once.
  final refresh = ValueNotifier<int>(0);
  ref.listen<SessionState>(sessionControllerProvider, (previous, next) {
    refresh.value++;
  });

  final router = GoRouter(
    initialLocation: AppRoutes.splash,
    refreshListenable: refresh,
    redirect: (context, state) => _redirect(ref.read(sessionControllerProvider), state),
    routes: [
      GoRoute(path: AppRoutes.splash, builder: (_, _) => const SplashScreen()),
      GoRoute(path: AppRoutes.login, builder: (_, _) => const LoginScreen()),
      GoRoute(
        path: AppRoutes.otp,
        builder: (_, state) => OtpScreen(phone: state.extra as String? ?? ''),
      ),
      GoRoute(path: AppRoutes.profileSetup, builder: (_, _) => const SignupScreen()),
      ShellRoute(
        builder: (context, state, child) => AppShell(child: child),
        routes: [
          GoRoute(path: AppRoutes.home, builder: (_, _) => const HomeScreen()),
          GoRoute(path: AppRoutes.history, builder: (_, _) => const HistoryScreen()),
          GoRoute(path: AppRoutes.profile, builder: (_, _) => const ProfileScreen()),
        ],
      ),
      GoRoute(path: AppRoutes.search, builder: (_, _) => const LocationSearchScreen()),
      GoRoute(
        path: '/ride/:id',
        builder: (_, state) => RideScreen(rideId: state.pathParameters['id']!),
      ),
      GoRoute(path: AppRoutes.editProfile, builder: (_, _) => const EditProfileScreen()),
      GoRoute(path: AppRoutes.settings, builder: (_, _) => const SettingsScreen()),
      GoRoute(path: AppRoutes.notifications, builder: (_, _) => const NotificationsScreen()),
      GoRoute(
        path: AppRoutes.support,
        builder: (_, state) => SupportScreen(rideId: state.extra as String?),
      ),
      GoRoute(path: AppRoutes.emergency, builder: (_, _) => const EmergencyScreen()),
    ],
  );

  ref.onDispose(() {
    router.dispose();
    refresh.dispose();
  });
  return router;
});

String? _redirect(SessionState session, GoRouterState state) {
  final location = state.matchedLocation;

  switch (session.status) {
    case SessionStatus.unknown:
      return location == AppRoutes.splash ? null : AppRoutes.splash;

    case SessionStatus.signedOut:
      if (location == AppRoutes.login) return null;
      // The OTP screen needs the phone number it was given.
      if (location == AppRoutes.otp && state.extra is String) return null;
      return AppRoutes.login;

    case SessionStatus.signedIn:
      if (session.needsProfile) {
        return location == AppRoutes.profileSetup ? null : AppRoutes.profileSetup;
      }
      const authOnly = [AppRoutes.splash, AppRoutes.login, AppRoutes.otp, AppRoutes.profileSetup];
      return authOnly.contains(location) ? AppRoutes.home : null;
  }
}
