from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.utils.translation import gettext_lazy as _


class ActiveUserManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))

        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


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
    ACTION_CHOICES = (
        ('create', 'CREATE'),
        ('read', 'READ'),
        ('update', 'UPDATE'),
        ('delete', 'DELETE'),
    )

    name = models.CharField(max_length=50)
    slug = models.CharField(
        max_length=50,
        unique=True,
        choices=ACTION_CHOICES
    )

    def __str__(self):
        return self.name


class Permission(models.Model):
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='permissions'
    )

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='permissions'
    )

    action = models.ForeignKey(
        Action,
        on_delete=models.CASCADE,
        related_name='permissions'
    )

    class Meta:
        unique_together = ('role', 'resource', 'action')

    def __str__(self):
        return (
            f'{self.role.slug} -> '
            f'{self.action.slug} -> '
            f'{self.resource.slug}'
        )


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        _('email address'),
        unique=True
    )

    full_name = models.CharField(max_length=255)

    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    objects = ActiveUserManager()
    all_objects = models.Manager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def delete(self, using=None, keep_parents=False):
        self.is_active = False
        self.save(update_fields=['is_active'])

    def has_resource_permission(self, resource_slug, action_slug):
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
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )

    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)

    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    hire_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.full_name} - {self.position}'

class BlacklistedToken(models.Model):
    token = models.CharField(max_length=500, unique=True)
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Blacklisted at {self.blacklisted_at}"