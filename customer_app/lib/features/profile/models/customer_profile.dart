/// Matches customers/profile/ in the backend.
class CustomerProfile {
  const CustomerProfile({
    required this.phone,
    required this.firstName,
    required this.lastName,
    this.email,
    this.emergencyContactName = '',
    this.emergencyContactPhone = '',
  });

  factory CustomerProfile.fromJson(Map<String, dynamic> json) {
    return CustomerProfile(
      phone: (json['phone'] as String?) ?? '',
      firstName: (json['first_name'] as String?) ?? '',
      lastName: (json['last_name'] as String?) ?? '',
      email: json['email'] as String?,
      emergencyContactName: (json['emergency_contact_name'] as String?) ?? '',
      emergencyContactPhone: (json['emergency_contact_phone'] as String?) ?? '',
    );
  }

  final String phone;
  final String firstName;
  final String lastName;
  final String? email;
  final String emergencyContactName;
  final String emergencyContactPhone;

  String get fullName => '$firstName $lastName'.trim();
}
