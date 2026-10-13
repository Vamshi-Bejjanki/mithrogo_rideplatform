from rest_framework import generics

from apps.customers.serializers import CustomerProfileSerializer
from apps.customers.services import ensure_profile
from apps.users.permissions import IsCustomer


class CustomerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsCustomer]

    def get_object(self):
        return ensure_profile(self.request.user)
