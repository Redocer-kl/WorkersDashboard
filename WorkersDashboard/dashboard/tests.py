from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from dashboard.models import User, Role, Resource, Action, Permission


class RbacTrafficTests(APITestCase):
    def setUp(self):
        self.role_admin = Role.objects.create(name='Admin', slug='admin')
        self.role_manager = Role.objects.create(name='Manager', slug='manager')
        self.role_guest = Role.objects.create(name='Guest', slug='guest')

        self.res_employees = Resource.objects.create(name='Employees', slug='employees')
        self.res_permissions = Resource.objects.create(name='Permissions', slug='permissions')

        self.act_read = Action.objects.create(name='Read', slug='read')
        self.act_create = Action.objects.create(name='Create', slug='create')
        self.act_update = Action.objects.create(name='Update', slug='update')
        self.act_delete = Action.objects.create(name='Delete', slug='delete')

        Permission.objects.create(
            role=self.role_manager,
            resource=self.res_employees,
            action=self.act_read
        )

        Permission.objects.create(
            role=self.role_admin,
            resource=self.res_permissions,
            action=self.act_read
        )
        Permission.objects.create(
            role=self.role_admin,
            resource=self.res_permissions,
            action=self.act_create
        )
        Permission.objects.create(
            role=self.role_admin,
            resource=self.res_permissions,
            action=self.act_update
        )
        Permission.objects.create(
            role=self.role_admin,
            resource=self.res_permissions,
            action=self.act_delete
        )

        self.manager = User.objects.create_user(
            email='manager@test.com',
            password='password123',
            full_name='Manager User',
            role=self.role_manager
        )

        self.guest = User.objects.create_user(
            email='guest@test.com',
            password='password123',
            full_name='Guest User',
            role=self.role_guest
        )

        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='password123',
            full_name='Admin User',
            role=self.role_admin,
            is_staff=True,
            is_superuser=False
        )

    def test_registration_passwords_dont_match(self):
        url = reverse('register')
        data = {
            'full_name': 'New User',
            'email': 'new@test.com',
            'password': 'password123',
            'password_repeat': 'different_pass'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_success(self):
        url = reverse('register')
        data = {
            'full_name': 'New User',
            'email': 'new@test.com',
            'password': 'ComplexPass123!',  
            'password_repeat': 'ComplexPass123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.all_objects.filter(email='new@test.com').exists())

    def test_login_success(self):
        url = reverse('login')
        response = self.client.post(
            url,
            {'email': 'manager@test.com', 'password': 'password123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_wrong_password(self):
        url = reverse('login')
        response = self.client.post(
            url,
            {'email': 'manager@test.com', 'password': 'wrong-password'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_resource_without_token_is_unauthorized(self):
        url = reverse('employee-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_and_access_resource(self):
        login_url = reverse('login')
        login_response = self.client.post(
            login_url,
            {'email': 'manager@test.com', 'password': 'password123'},
            format='json'
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        token = login_response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

        url = reverse('employee-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_token_is_unauthorized(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        url = reverse('employee-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_forbidden_for_user_without_permission(self):
        self.client.force_authenticate(user=self.guest)
        url = reverse('employee-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_soft_delete(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('profile')

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        user_in_db = User.all_objects.get(email='manager@test.com')
        self.assertFalse(user_in_db.is_active)

        login_url = reverse('login')
        response = self.client.post(
            login_url,
            {'email': 'manager@test.com', 'password': 'password123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_update(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('profile')
        data = {
            'full_name': 'Updated Manager',
            'email': 'manager@test.com'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.manager.refresh_from_db()
        self.assertEqual(self.manager.full_name, 'Updated Manager')

    def test_non_admin_cannot_manage_permissions(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('permission-list')
        data = {
            'role': self.role_manager.id,
            'resource': self.res_permissions.id,
            'action': self.act_read.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_manage_permissions(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('permission-list')
        data = {
        'role': self.role_admin.id,
        'resource': self.res_employees.id,
        'action': self.act_create.id       
    }
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    def test_logout_blacklists_token(self):
        """
        Проверка: после логаута токен добавляется в blacklist, 
        и по нему больше нельзя получить доступ к ресурсам.
        """

        login_url = reverse('login')
        login_response = self.client.post(
            login_url,
            {'email': 'manager@test.com', 'password': 'password123'},
            format='json'
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        token = login_response.data['token']
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        employees_url = reverse('employee-list')
        response_before_logout = self.client.get(employees_url)
        self.assertEqual(response_before_logout.status_code, status.HTTP_200_OK)

        logout_url = reverse('logout')  # Убедись, что имя url 'logout' совпадает с твоим urls.py
        logout_response = self.client.post(logout_url)
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        response_after_logout = self.client.get(employees_url)

        self.assertEqual(response_after_logout.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response_after_logout.data['detail'], 
            'Token has been blacklisted (Logged out)'
        )