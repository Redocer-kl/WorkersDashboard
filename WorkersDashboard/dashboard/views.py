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

import logging
logger = logging.getLogger('dashboard') 


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        logger.info(f"New user registered: {user.email} (ID: {user.id})")


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
            logger.info(f"Successful login: {email}")
            return Response({'token': token, 'user': UserSerializer(user).data})
        
        logger.warning(f"Failed login attempt for email: {email}")
        return Response(
            {'error': 'Invalid credentials or account deleted'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"User logged out: {request.user.email}")
        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        user = serializer.save()
        logger.info(f"User profile updated: {user.email}")

    def perform_destroy(self, instance):
        logger.info(f"User profile deleted by owner: {instance.email}")
        instance.delete() 


class AdminPermissionViewSet(viewsets.ModelViewSet):
    """
    Эндпоинт для админа. Здесь аудит особенно важен.
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        perm = serializer.save()
        logger.info(f"Admin {self.request.user.email} created permission: {perm.name}")

    def perform_update(self, serializer):
        perm = serializer.save()
        logger.info(f"Admin {self.request.user.email} updated permission: {perm.name}")

    def perform_destroy(self, instance):
        logger.warning(f"Admin {self.request.user.email} DELETED permission: {instance.name}")
        instance.delete()


class EmployeeListView(generics.ListAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [HasResourcePermission]
    resource_slug = 'employees'
    
    def list(self, request, *args, **kwargs):
        logger.debug(f"Employee list accessed by: {request.user.email}")
        return super().list(request, *args, **kwargs)