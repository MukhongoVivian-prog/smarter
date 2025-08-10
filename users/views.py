from rest_framework import generics, permissions
from .models import User
from .serializers import UserSerializer, RegisterSerializer
from .permissions import IsLandlord, IsTenant, IsAdmin

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class LandlordOnlyView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsLandlord]

class TenantOnlyView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsTenant]
