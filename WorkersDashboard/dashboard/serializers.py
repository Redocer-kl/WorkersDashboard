from rest_framework import serializers
from .models import User, Role, Permission, Resource, Action, Employee
from django.contrib.auth.password_validation import validate_password

# --- 1. Регистрация (с повтором пароля по ТЗ) ---
class RegisterSerializer(serializers.ModelSerializer):
    password_repeat = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('full_name', 'email', 'password', 'password_repeat')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        # Проверка совпадения паролей согласно ТЗ 
        if data['password'] != data['password_repeat']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        validate_password(data['password'])
        return data

    def create(self, validated_data):
        validated_data.pop('password_repeat')
        # Создаем пользователя через наш менеджер (пароль захешируется сам)
        user = User.objects.create_user(**validated_data)
        return user

# --- 2. Логин ---
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

# --- 3. Профиль пользователя (чтение и обновление) ---
class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'role_name')
        read_only_fields = ('email',) # Обычно email не дают менять просто так

# --- 4. Управление правами (для Админа) ---
class PermissionSerializer(serializers.ModelSerializer):
    """Сериализатор для API управления правилами доступа """
    class Meta:
        model = Permission
        fields = '__all__'

# --- 5. Вымышленные объекты (Mock) ---
class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'