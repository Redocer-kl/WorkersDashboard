from django.core.management.base import BaseCommand
from dashboard.models import Role, Resource, Action, Permission, User, Employee

class Command(BaseCommand):
    help = 'Заполняет базу данных начальными данными для тестирования RBAC'

    def handle(self, *args, **options):
        self.stdout.write('Заполнение данных...')

        actions_data = ['create', 'read', 'update', 'delete']
        actions = {}
        for a_slug in actions_data:
            obj, _ = Action.objects.get_or_create(slug=a_slug, defaults={'name': a_slug.upper()})
            actions[a_slug] = obj

        resources_data = ['employees', 'permissions', 'salary']
        resources = {}
        for r_slug in resources_data:
            obj, _ = Resource.objects.get_or_create(slug=r_slug, defaults={'name': r_slug.capitalize()})
            resources[r_slug] = obj

        admin_role, _ = Role.objects.get_or_create(slug='admin', name='Administrator')
        manager_role, _ = Role.objects.get_or_create(slug='manager', name='Manager')

        
        for res in resources.values():
            for act in actions.values():
                Permission.objects.get_or_create(role=admin_role, resource=res, action=act)

        Permission.objects.get_or_create(
            role=manager_role, 
            resource=resources['employees'], 
            action=actions['read']
        )

        if not User.objects.filter(email='admin@test.com').exists():
            admin_user = User.objects.create_user(
                email='admin@test.com', 
                password='password123', 
                full_name='Главный Админ',
                role=admin_role,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS('Создан админ: admin@test.com / password123'))

        if not User.objects.filter(email='manager@test.com').exists():
            manager_user = User.objects.create_user(
                email='manager@test.com', 
                password='password123', 
                full_name='Иван Менеджеров',
                role=manager_role
            )
            Employee.objects.create(user=manager_user, department='Sales', position='Lead', salary=50000)
            self.stdout.write(self.style.SUCCESS('Создан менеджер: manager@test.com / password123'))

        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена!'))