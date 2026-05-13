from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _

# --- Менеджеры ---

class CustomUserManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

# --- RBAC Модели  ---

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Resource(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True) 

    def __str__(self):
        return self.name

class Action(models.Model):
    name = models.CharField(max_length=50) # CREATE, READ, UPDATE, DELETE
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Permission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    action = models.ForeignKey(Action, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'resource', 'action')

    def __str__(self):
        return f"{self.role.name} -> {self.action.slug} on {self.resource.slug}"

# --- Модель Пользователя ---

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = CustomUserManager()
    all_objects = models.Manager() 

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def delete(self, **kwargs):
        self.is_active = False
        self.save()

    def has_resource_permission(self, resource_slug, action_slug):
        """
        Собственная система проверки доступа.
        Проверяет, есть ли у роли пользователя право на действие с ресурсом.
        """
        if self.is_superuser:
            return True
        if not self.role:
            return False
            
        return Permission.objects.filter(
            role=self.role,
            resource__slug=resource_slug,
            action__slug=action_slug
        ).exists()

    def __str__(self):
        return self.email

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2) 
    hire_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.position}"