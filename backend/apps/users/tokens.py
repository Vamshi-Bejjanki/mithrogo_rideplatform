from rest_framework_simplejwt.tokens import RefreshToken


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    return {"access": str(refresh.access_token), "refresh": str(refresh)}
