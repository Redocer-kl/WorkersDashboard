from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, LogoutView, 
    UserProfileView, AdminPermissionViewSet, EmployeeListView
)

router = DefaultRouter()
router.register(r'admin/permissions', AdminPermissionViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('employees/', EmployeeListView.as_view(), name='employee-list'),
    path('', include(router.urls)),
]