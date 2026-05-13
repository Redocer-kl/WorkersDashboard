from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate

from .models import User, Permission, Employee
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer, 
    PermissionSerializer, EmployeeSerializer
)
from .security import generate_access_token
from .permissions import HasResourcePermission


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(request=request, email=email, password=password)
        
        if user and user.is_active:
            token = generate_access_token(user)
            return Response({'token': token, 'user': UserSerializer(user).data})
        
        return Response(
            {'error': 'Invalid credentials or account deleted'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        instance.delete() 


class AdminPermissionViewSet(viewsets.ModelViewSet):
    """
    Эндпоинт для админа, чтобы менять правила доступа.
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]


class EmployeeListView(generics.ListAPIView):
    """
    Пример ресурса, защищенного твоей RBAC системой.
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [HasResourcePermission]
    resource_slug = 'employees' 