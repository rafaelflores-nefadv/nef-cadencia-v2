"""
Management command para criar dados iniciais de workspaces.

Uso:
    python manage.py seed_workspaces
    python manage.py seed_workspaces --clear  # Limpa dados existentes antes
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.workspaces.models import Workspace, UserWorkspace

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria dados iniciais de workspaces para desenvolvimento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpa workspaces existentes antes de criar novos',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Limpando workspaces existentes...')
            UserWorkspace.objects.all().delete()
            Workspace.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Workspaces limpos'))

        self.stdout.write('Criando workspaces iniciais...')

        with transaction.atomic():
            # Criar workspaces
            workspace_principal = self._create_workspace(
                name='Workspace Principal',
                slug='principal',
                description='Ambiente principal de produção'
            )

            workspace_testes = self._create_workspace(
                name='Workspace de Testes',
                slug='testes',
                description='Ambiente de testes e desenvolvimento'
            )

            workspace_comercial = self._create_workspace(
                name='Workspace Comercial',
                slug='comercial',
                description='Equipe comercial e vendas'
            )

            # Buscar ou criar usuário admin
            admin_user = self._get_or_create_admin()

            # Adicionar admin aos workspaces
            self._add_member(workspace_principal, admin_user, UserWorkspace.Role.ADMIN)
            self._add_member(workspace_testes, admin_user, UserWorkspace.Role.ADMIN)
            self._add_member(workspace_comercial, admin_user, UserWorkspace.Role.ADMIN)

            # Criar usuários de teste
            user_teste1 = self._get_or_create_user(
                username='usuario1',
                email='usuario1@example.com',
                first_name='Usuário',
                last_name='Um'
            )
            self._add_member(workspace_principal, user_teste1, UserWorkspace.Role.MEMBER)
            self._add_member(workspace_testes, user_teste1, UserWorkspace.Role.MEMBER)

            user_teste2 = self._get_or_create_user(
                username='usuario2',
                email='usuario2@example.com',
                first_name='Usuário',
                last_name='Dois'
            )
            self._add_member(workspace_principal, user_teste2, UserWorkspace.Role.VIEWER)
            self._add_member(workspace_comercial, user_teste2, UserWorkspace.Role.MEMBER)

            # Definir workspace padrão para admin
            admin_user.set_default_workspace(workspace_principal)

        self.stdout.write(self.style.SUCCESS('✓ Workspaces criados com sucesso!'))
        self.stdout.write('')
        self.stdout.write('Workspaces criados:')
        self.stdout.write(f'  • {workspace_principal.name} ({workspace_principal.slug})')
        self.stdout.write(f'  • {workspace_testes.name} ({workspace_testes.slug})')
        self.stdout.write(f'  • {workspace_comercial.name} ({workspace_comercial.slug})')
        self.stdout.write('')
        self.stdout.write('Usuários:')
        self.stdout.write(f'  • admin (admin em todos os workspaces)')
        self.stdout.write(f'  • usuario1 (membro em principal e testes)')
        self.stdout.write(f'  • usuario2 (visualizador em principal, membro em comercial)')

    def _create_workspace(self, name, slug, description):
        """Cria ou atualiza um workspace."""
        workspace, created = Workspace.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'description': description,
                'is_active': True
            }
        )
        
        if not created:
            workspace.name = name
            workspace.description = description
            workspace.is_active = True
            workspace.save()
            self.stdout.write(f'  ↻ Workspace atualizado: {name}')
        else:
            self.stdout.write(f'  ✓ Workspace criado: {name}')
        
        return workspace

    def _get_or_create_admin(self):
        """Busca ou cria usuário admin."""
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'Sistema',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(f'  ✓ Usuário admin criado (senha: admin123)')
        else:
            self.stdout.write(f'  ↻ Usuário admin já existe')
        
        return admin_user

    def _get_or_create_user(self, username, email, first_name, last_name):
        """Busca ou cria usuário comum."""
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True
            }
        )
        
        if created:
            user.set_password('senha123')
            user.save()
            self.stdout.write(f'  ✓ Usuário {username} criado (senha: senha123)')
        else:
            self.stdout.write(f'  ↻ Usuário {username} já existe')
        
        return user

    def _add_member(self, workspace, user, role):
        """Adiciona membro ao workspace."""
        membership, created = UserWorkspace.objects.get_or_create(
            workspace=workspace,
            user=user,
            defaults={'role': role}
        )
        
        if not created and membership.role != role:
            membership.role = role
            membership.save()
