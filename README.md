# Workers Dashboard Backend

Backend-приложение для управления доступом сотрудников, реализующее собственную систему аутентификации и ролевую модель авторизации (RBAC — Role-Based Access Control) без использования готовых решений для управления правами доступа.

## Основной функционал

- **Собственная система JWT-аутентификации:** генерация и валидация токенов реализованы кастомно.
- **Кастомная авторизация (RBAC):** динамическая проверка прав доступа на основе связей «Роль → Ресурс → Действие».
- **Мягкое удаление (Soft Delete):** безопасное удаление профиля без потери связанных данных (`is_active = False`) с автоматической инвалидацией активных сессий и токенов.
- **API для управления:** интерфейс для администраторов по управлению правилами доступа.

## Архитектура системы доступа (схема БД)

Система управления доступом построена на 4 основных моделях:

1. **`Role` (роль):** группа прав (например, `admin`, `manager`, `guest`). Пользователь имеет связь `ForeignKey` с ролью.
2. **`Resource` (ресурс):** логическая сущность или таблица (например, `employees`, `salary_reports`).
3. **`Action` (действие):** CRUD-операции (например, `create`, `read`, `update`, `delete`).
4. **`Permission` (разрешение):** связующая таблица, определяющая, что конкретная **роль** имеет право совершить конкретное **действие** над конкретным **ресурсом**.

### ER-диаграмма связей

```text
[ User ] (1) ------ (M) [ Role ]
                           | (1)
                           |
                           | (M)
                     [ Permission ]
                      (M)      (M)
                      /          \
                    (1)          (1)
             [ Resource ]      [ Action ]
```

### Как это работает

При обращении к защищенному эндпоинту (например, `/employees/`) кастомный permission-класс `HasResourcePermission` проверяет:

1. Идентифицирован ли пользователь по токену.
2. Какая роль назначена пользователю.
3. Существует ли запись в таблице `Permission`, где:
   - `role` = роль пользователя;
   - `resource` = `employees` (указывается во View);
   - `action` = `read` (определяется по HTTP-методу, например `GET`).

Если запись найдена — доступ разрешен. Если нет — возвращается ошибка `403 Forbidden`.

## Структура API (эндпоинты и Views)

Доступен Swagger/ReDoc (при подключенном `drf-spectacular`) по стандартным путям.

### Основные эндпоинты

| Эндпоинт | HTTP-метод | View | Описание | Доступ |
|---|---:|---|---|---|
| `/register/` | `POST` | `RegisterView` | Регистрация пользователя (с проверкой совпадения паролей). | `AllowAny` |
| `/login/` | `POST` | `LoginView` | Вход по email и паролю. Возвращает кастомный JWT. | `AllowAny` |
| `/logout/` | `POST` | `LogoutView` | Выход из системы. | `IsAuthenticated` |
| `/profile/` | `GET, PUT, PATCH` | `UserProfileView` | Получение и обновление данных профиля. | `IsAuthenticated` |
| `/profile/` | `DELETE` | `UserProfileView` | Мягкое удаление аккаунта (logout). | `IsAuthenticated` |
| `/admin/permissions/` | `GET, POST, PUT, DELETE` | `AdminPermissionViewSet` | CRUD-управление правилами доступа. | `IsAuthenticated / Admin` |
| `/employees/` | `GET` | `EmployeeListView` | Mock-ресурс бизнес-логики. | `RBAC (employees -> read)` |

## Настройка окружения (шаблон `.env`)

Для запуска проекта создайте файл `.env` в корневой директории и заполните его по следующему шаблону.

```env
# --- Базовые настройки Django ---
SECRET_KEY=your-django-insecure-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# --- Настройки базы данных (PostgreSQL) ---
DB_NAME=auth_system_db
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_HOST=db
DB_PORT=5432

# --- Безопасность и JWT ---
# Уникальная соль для дополнительного хэширования (можно сгенерировать через secrets.token_hex(32))
PASSWORD_HASHERS_SALT=generate-a-random-string-for-salt
# Ключ для подписи ваших кастомных JWT-токенов
JWT_SECRET_KEY=another-very-secret-key-specifically-for-jwt
```

# Тестирование

Проект покрыт интеграционными тестами (`APITestCase`), которые проверяют корректность работы JWT-аутентификации, логику RBAC и строгое соответствие ТЗ по статус-кодам.

## Запуск тестов

Для запуска тестов внутри Docker-контейнера используйте команду:

```bash
docker compose exec web python manage.py test
```

## Описание тест-кейсов

| Категория | Тест-кейс                                  | Описание проверки                                                     | Ожидаемый статус |
| -----------| --------------------------------------------| -----------------------------------------------------------------------| ------------------|
| Auth      | `test_registration_success`                | Регистрация с валидными данными и сложным паролем.                    | 201 Created      |
| Auth      | `test_registration_passwords_dont_match`   | Попытка регистрации с несовпадающими паролями.                        | 400 Bad Request  |
| Auth      | `test_login_success`                       | Вход по верным учетным данным и получение JWT-токена.                 | 200 OK           |
| Auth      | `test_login_wrong_password`                | Попытка входа с неверным паролем.                                     | 401 Unauthorized |
| Auth      | `test_invalid_token_is_unauthorized`       | Запрос к защищенному API с поддельным/битым токеном.                  | 401 Unauthorized |
| Auth      | `test_access_resource_without_token`       | Запрос к API без заголовка `Authorization`.                           | 401 Unauthorized |
| Profile   | `test_profile_update`                      | Обновление данных (имя) текущего залогиненного пользователя.          | 200 OK           |
| Profile   | `test_soft_delete`                         | Мягкое удаление профиля (`is_active=False`) и проверка запрета входа. | 204 No Content   |
| RBAC      | `test_login_and_access_resource`           | Успешный доступ к ресурсу при наличии прав в таблице `Permission`.    | 200 OK           |
| RBAC      | `test_access_forbidden_no_permission`      | Отказ в доступе пользователю, роль которого не имеет прав на ресурс.  | 403 Forbidden    |
| Admin     | `test_admin_can_manage_permissions`        | Возможность администратора создавать новые правила доступа.           | 201 Created      |
| Admin     | `test_non_admin_cannot_manage_permissions` | Запрет обычным пользователям (менеджерам) управлять правами.          | 403 Forbidden    |
| Auth      | `test_logout_blacklists_token` | Проверка того, что после logout токен попадает в черный список и доступ к API по нему блокируется. | 401 Unauthorized