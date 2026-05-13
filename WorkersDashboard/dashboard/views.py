from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.hashers import check_password

from .models import User, Permission, Employee, BlacklistedToken
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    PermissionSerializer,
    EmployeeSerializer
)
from .security import generate_access_token
from .permissions import HasResourcePermission, IsAdminUserRole

import logging

logger = logging.getLogger('dashboard')


class RegisterView(generics.CreateAPIView):
    queryset = User.all_objects.all()
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

        try:
            user = User.all_objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"Failed login attempt for email: {email}")

            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'Account is deactivated'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not check_password(password, user.password):
            logger.warning(f"Failed login attempt for email: {email}")

            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token = generate_access_token(user)

        logger.info(f"Successful login: {email}")

        return Response({
            'token': token,
            'user': UserSerializer(user).data
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Достаем токен из заголовка
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split(' ')
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                BlacklistedToken.objects.get_or_create(token=token)

        logger.info(f"User logged out: {request.user.email}")

        return Response(
            {"message": "Successfully logged out"},
            status=status.HTTP_200_OK
        )


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
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def perform_create(self, serializer):
        perm = serializer.save()

        logger.info(
            f"Admin {self.request.user.email} created permission: "
            f"{perm.role.slug} -> {perm.action.slug} -> {perm.resource.slug}"
        )

    def perform_update(self, serializer):
        perm = serializer.save()

        logger.info(
            f"Admin {self.request.user.email} updated permission: "
            f"{perm.role.slug} -> {perm.action.slug} -> {perm.resource.slug}"
        )

    def perform_destroy(self, instance):
        logger.warning(
            f"Admin {self.request.user.email} deleted permission: "
            f"{instance.role.slug} -> {instance.action.slug} -> {instance.resource.slug}"
        )

        instance.delete()


class EmployeeListView(generics.ListAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [HasResourcePermission]
    resource_slug = 'employees'

    def list(self, request, *args, **kwargs):
        logger.debug(f"Employee list accessed by: {request.user.email}")

        return super().list(request, *args, **kwargs)