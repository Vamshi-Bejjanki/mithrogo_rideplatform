/// Values from the profile form. Blank strings are sent as blanks, which the backend stores as empty or NULL.
class ProfileInput {
  const ProfileInput({
    required this.firstName,
    required this.lastName,
    required this.email,
    required this.emergencyContactName,
    required this.emergencyContactPhone,
  });

  final String firstName;
  final String lastName;
  final String email;
  final String emergencyContactName;
  final String emergencyContactPhone;

  Map<String, dynamic> toJson() => {
        'first_name': firstName,
        'last_name': lastName,
        'email': email,
        'emergency_contact_name': emergencyContactName,
        'emergency_contact_phone': emergencyContactPhone,
      };
}
