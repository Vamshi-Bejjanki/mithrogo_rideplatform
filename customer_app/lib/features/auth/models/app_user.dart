/// The signed-in user, as returned by auth/verify-otp/ and auth/me/.
class AppUser {
  const AppUser({
    required this.id,
    required this.phone,
    required this.firstName,
    required this.lastName,
    this.email,
  });

  factory AppUser.fromJson(Map<String, dynamic> json) {
    return AppUser(
      id: json['id'].toString(),
      phone: json['phone'] as String,
      firstName: (json['first_name'] as String?) ?? '',
      lastName: (json['last_name'] as String?) ?? '',
      email: json['email'] as String?,
    );
  }

  final String id;
  final String phone;
  final String firstName;
  final String lastName;
  final String? email;

  /// A new customer has no name yet. The signup (profile setup) screen fills it in.
  bool get needsProfile => firstName.trim().isEmpty;
}
