"""
Testes para o sistema de permissões.

Testa mixins, decorators e helpers de autorização.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from apps.core.permissions_advanced import (
    user_can_access_dashboard,
    user_can_manage_settings,
    user_can_manage_integrations,
    user_can_manage_rules,
    user_can_manage_users,
    user_can_manage_assistant,
    user_can_view_reports,
    user_can_access_monitoring,
    get_user_permissions_summary,
)


User = get_user_model()


class PermissionHelpersTests(TestCase):
    """Testes para os helpers de permissão."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        # Criar usuário regular
        self.regular_user = User.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
        
        # Criar usuário staff
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        
        # Criar usuário superuser
        self.superuser = User.objects.create_user(
            username='superuser',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Criar grupos
        self.operadores_group = Group.objects.create(name='Operadores')
        self.admin_group = Group.objects.create(name='Administradores')
        self.admin_sistema_group = Group.objects.create(name='Administradores de Sistema')
        
        # Criar permissões customizadas
        content_type = ContentType.objects.get_or_create(
            app_label='core',
            model='customperms'
        )[0]
        
        self.manage_settings_perm = Permission.objects.get_or_create(
            codename='manage_settings',
            name='Can manage system settings',
            content_type=content_type
        )[0]
        
        # Criar usuário com grupo
        self.group_user = User.objects.create_user(
            username='groupuser',
            password='testpass123',
            is_staff=False
        )
        self.group_user.groups.add(self.operadores_group)
    
    def test_user_can_access_dashboard_staff(self):
        """Testa que staff pode acessar dashboard."""
        self.assertTrue(user_can_access_dashboard(self.staff_user))
    
    def test_user_can_access_dashboard_group(self):
        """Testa que usuário do grupo Operadores pode acessar dashboard."""
        self.assertTrue(user_can_access_dashboard(self.group_user))
    
    def test_user_can_access_dashboard_regular_denied(self):
        """Testa que usuário regular sem grupo não pode acessar dashboard."""
        self.assertFalse(user_can_access_dashboard(self.regular_user))
    
    def test_user_can_manage_settings_staff(self):
        """Testa que staff pode gerenciar configurações."""
        self.assertTrue(user_can_manage_settings(self.staff_user))
    
    def test_user_can_manage_settings_group(self):
        """Testa que usuário do grupo Administradores pode gerenciar configurações."""
        self.group_user.groups.add(self.admin_group)
        self.assertTrue(user_can_manage_settings(self.group_user))
    
    def test_user_can_manage_settings_regular_denied(self):
        """Testa que usuário regular não pode gerenciar configurações."""
        self.assertFalse(user_can_manage_settings(self.regular_user))
    
    def test_user_can_manage_users_superuser(self):
        """Testa que superuser pode gerenciar usuários."""
        self.assertTrue(user_can_manage_users(self.superuser))
    
    def test_user_can_manage_users_group(self):
        """Testa que usuário do grupo Admin de Sistema pode gerenciar usuários."""
        self.group_user.groups.add(self.admin_sistema_group)
        self.assertTrue(user_can_manage_users(self.group_user))
    
    def test_user_can_manage_users_staff_denied(self):
        """Testa que staff comum não pode gerenciar usuários."""
        self.assertFalse(user_can_manage_users(self.staff_user))
    
    def test_get_user_permissions_summary_staff(self):
        """Testa resumo de permissões para staff."""
        summary = get_user_permissions_summary(self.staff_user)
        
        self.assertIsInstance(summary, dict)
        self.assertIn('can_access_dashboard', summary)
        self.assertIn('can_manage_settings', summary)
        self.assertIn('is_staff', summary)
        self.assertIn('is_superuser', summary)
        
        # Staff deve ter acesso a dashboard e configurações
        self.assertTrue(summary['can_access_dashboard'])
        self.assertTrue(summary['can_manage_settings'])
        self.assertTrue(summary['is_staff'])
        self.assertFalse(summary['is_superuser'])
    
    def test_get_user_permissions_summary_regular(self):
        """Testa resumo de permissões para usuário regular."""
        summary = get_user_permissions_summary(self.regular_user)
        
        # Usuário regular não deve ter permissões
        self.assertFalse(summary['can_access_dashboard'])
        self.assertFalse(summary['can_manage_settings'])
        self.assertFalse(summary['is_staff'])
        self.assertFalse(summary['is_superuser'])
    
    def test_get_user_permissions_summary_superuser(self):
        """Testa resumo de permissões para superuser."""
        summary = get_user_permissions_summary(self.superuser)
        
        # Superuser deve ter todas as permissões
        self.assertTrue(summary['can_access_dashboard'])
        self.assertTrue(summary['can_manage_settings'])
        self.assertTrue(summary['can_manage_users'])
        self.assertTrue(summary['is_staff'])
        self.assertTrue(summary['is_superuser'])


class PermissionMixinsIntegrationTests(TestCase):
    """Testes de integração para mixins de permissão."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.factory = RequestFactory()
        
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
    
    def test_configuration_access_mixin_allows_staff(self):
        """Testa que ConfigurationAccessMixin permite staff."""
        from apps.core.permissions_advanced import ConfigurationAccessMixin
        from django.views.generic import TemplateView
        
        class TestView(ConfigurationAccessMixin, TemplateView):
            template_name = 'test.html'
        
        request = self.factory.get('/test/')
        request.user = self.staff_user
        
        view = TestView()
        view.request = request
        
        # Staff deve passar no teste
        self.assertTrue(view.test_func())
    
    def test_configuration_access_mixin_blocks_regular(self):
        """Testa que ConfigurationAccessMixin bloqueia usuário regular."""
        from apps.core.permissions_advanced import ConfigurationAccessMixin
        from django.views.generic import TemplateView
        
        class TestView(ConfigurationAccessMixin, TemplateView):
            template_name = 'test.html'
        
        request = self.factory.get('/test/')
        request.user = self.regular_user
        
        view = TestView()
        view.request = request
        
        # Regular user não deve passar no teste
        self.assertFalse(view.test_func())
    
    def test_user_management_mixin_allows_superuser(self):
        """Testa que UserManagementMixin permite superuser."""
        from apps.core.permissions_advanced import UserManagementMixin
        from django.views.generic import TemplateView
        
        superuser = User.objects.create_user(
            username='superuser',
            password='testpass123',
            is_superuser=True
        )
        
        class TestView(UserManagementMixin, TemplateView):
            template_name = 'test.html'
        
        request = self.factory.get('/test/')
        request.user = superuser
        
        view = TestView()
        view.request = request
        
        # Superuser deve passar no teste
        self.assertTrue(view.test_func())
    
    def test_user_management_mixin_blocks_staff(self):
        """Testa que UserManagementMixin bloqueia staff comum."""
        from apps.core.permissions_advanced import UserManagementMixin
        from django.views.generic import TemplateView
        
        class TestView(UserManagementMixin, TemplateView):
            template_name = 'test.html'
        
        request = self.factory.get('/test/')
        request.user = self.staff_user
        
        view = TestView()
        view.request = request
        
        # Staff comum não deve passar no teste
        self.assertFalse(view.test_func())


class ContextProcessorTests(TestCase):
    """Testes para o context processor de permissões."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.factory = RequestFactory()
        
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
    
    def test_context_processor_with_staff_user(self):
        """Testa context processor com usuário staff."""
        from apps.core.context_processors import user_permissions
        
        request = self.factory.get('/')
        request.user = self.staff_user
        
        context = user_permissions(request)
        
        # Verificar que as permissões estão no contexto
        self.assertIn('can_access_dashboard', context)
        self.assertIn('can_manage_settings', context)
        self.assertIn('user_permissions', context)
        
        # Staff deve ter permissões
        self.assertTrue(context['can_access_dashboard'])
        self.assertTrue(context['can_manage_settings'])
    
    def test_context_processor_with_regular_user(self):
        """Testa context processor com usuário regular."""
        from apps.core.context_processors import user_permissions
        
        request = self.factory.get('/')
        request.user = self.regular_user
        
        context = user_permissions(request)
        
        # Usuário regular não deve ter permissões
        self.assertFalse(context['can_access_dashboard'])
        self.assertFalse(context['can_manage_settings'])
    
    def test_context_processor_with_anonymous_user(self):
        """Testa context processor com usuário anônimo."""
        from apps.core.context_processors import user_permissions
        from django.contrib.auth.models import AnonymousUser
        
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        context = user_permissions(request)
        
        # Usuário anônimo não deve ter permissões
        self.assertFalse(context['can_access_dashboard'])
        self.assertFalse(context['can_manage_settings'])
