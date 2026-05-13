from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from dashboard.models import User, Role, Resource, Action, Permission

class RbacTrafficTests(APITestCase):
    def setUp(self):
        self.role_manager = Role.objects.create(name='Manager', slug='manager')
        self.res_employees = Resource.objects.create(name='Employees', slug='employees')
        self.act_read = Action.objects.create(name='Read', slug='read')
        
        Permission.objects.create(
            role=self.role_manager, 
            resource=self.res_employees, 
            action=self.act_read
        )
        
        self.user = User.objects.create_user(
            email='test@test.com', 
            password='password123',
            full_name='Test User',
            role=self.role_manager
        )

    def test_registration_passwords_dont_match(self):
        """Проверка требования ТЗ: ошибка при несовпадении паролей"""
        url = reverse('register')
        data = {
            "full_name": "New User",
            "email": "new@test.com",
            "password": "password123",
            "password_repeat": "different_pass"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_and_access_resource(self):
        """Проверка логина, получения кастомного JWT и доступа к Mock-View"""
        login_url = reverse('login')
        response = self.client.post(login_url, {'email': 'test@test.com', 'password': 'password123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['token']

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        url = reverse('employee-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_soft_delete(self):
        """Проверка мягкого удаления из ТЗ"""
        self.client.force_authenticate(user=self.user)
        url = reverse('profile')
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        user_in_db = User.all_objects.get(email='test@test.com')
        self.assertFalse(user_in_db.is_active)
        
        login_url = reverse('login')
        response = self.client.post(login_url, {'email': 'test@test.com', 'password': 'password123'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_forbidden(self):
        """Проверка требования ТЗ: ошибка 403, если нет прав"""
        role_guest = Role.objects.create(name='Guest', slug='guest')
        guest_user = User.objects.create_user(
            email='guest@test.com', password='password123', full_name='Guest', role=role_guest
        )
        
        self.client.force_authenticate(user=guest_user)
        url = reverse('employee-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)