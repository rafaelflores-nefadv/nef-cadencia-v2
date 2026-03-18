"""
Testes para as views de Configurações.

Testa acesso autenticado, bloqueio de usuários sem permissão,
renderização de templates e funcionamento das rotas.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType


class SettingsHubViewTests(TestCase):
    """Testes para a view principal de configurações (SettingsHubView)."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.client = Client()
        
        # Criar usuários
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
        
        # Criar grupo Administradores
        self.admin_group = Group.objects.create(name='Administradores')
        
        # Criar permissão customizada
        content_type = ContentType.objects.get_or_create(
            app_label='core',
            model='customperms'
        )[0]
        
        self.manage_settings_perm = Permission.objects.get_or_create(
            codename='manage_settings',
            name='Can manage system settings',
            content_type=content_type
        )[0]
        
        # Adicionar permissão ao grupo
        self.admin_group.permissions.add(self.manage_settings_perm)
        
        # Criar usuário com permissão via grupo
        self.group_user = User.objects.create_user(
            username='groupuser',
            password='testpass123',
            is_staff=False
        )
        self.group_user.groups.add(self.admin_group)
    
    def test_settings_hub_requires_authentication(self):
        """Testa que a página de configurações requer autenticação."""
        response = self.client.get(reverse('settings-hub'))
        
        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_settings_hub_blocks_user_without_permission(self):
        """Testa que usuário sem permissão é bloqueado."""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('settings-hub'))
        
        # Deve redirecionar com mensagem de erro
        self.assertEqual(response.status_code, 302)
        
        # Verificar mensagem de erro
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('permissão' in str(m).lower() for m in messages))
    
    def test_settings_hub_allows_staff_user(self):
        """Testa que usuário staff tem acesso."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('settings-hub'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/settings_hub.html')
    
    def test_settings_hub_allows_user_with_permission(self):
        """Testa que usuário com permissão via grupo tem acesso."""
        self.client.login(username='groupuser', password='testpass123')
        response = self.client.get(reverse('settings-hub'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/settings_hub.html')
    
    def test_settings_hub_renders_correct_template(self):
        """Testa que o template correto é renderizado."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('settings-hub'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/settings_hub.html')
        self.assertTemplateUsed(response, 'base.html')
    
    def test_settings_hub_context_contains_required_data(self):
        """Testa que o contexto contém todos os dados necessários."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('settings-hub'))
        
        # Verificar dados no contexto
        self.assertIn('system_configs', response.context)
        self.assertIn('operational_rules', response.context)
        self.assertIn('integrations', response.context)
        self.assertIn('message_templates', response.context)
        self.assertIn('assistant_config', response.context)
        self.assertIn('pause_classification', response.context)
        self.assertIn('user_management', response.context)
        self.assertIn('appearance', response.context)
        self.assertIn('health_overview', response.context)
        self.assertIn('alerts', response.context)
    
    def test_settings_hub_page_title(self):
        """Testa que o título da página está correto."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('settings-hub'))
        
        self.assertContains(response, 'Configurações')
        self.assertContains(response, 'Central de gerenciamento')


class SettingsChildPagesTests(TestCase):
    """Testes para as páginas filhas de configurações."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
    
    def test_settings_general_route_exists(self):
        """Testa que a rota /settings/general/ existe."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('settings-general'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_settings_rules_route_exists(self):
        """Testa que a rota /settings/rules/ existe."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('settings-rules'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_settings_integrations_route_exists(self):
        """Testa que a rota /settings/integrations/ existe."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('settings-integrations'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_settings_templates_route_exists(self):
        """Testa que a rota /settings/templates/ existe."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('settings-templates'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_settings_assistant_route_exists(self):
        """Testa que a rota /settings/assistant/ existe."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('settings-assistant'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_settings_pause_classification_route_exists(self):
        """Testa que a rota /settings/pause-classification/ existe."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('settings-pause-classification'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_settings_users_route_exists(self):
        """Testa que a rota /settings/users/ existe."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('settings-users'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_child_pages_require_authentication(self):
        """Testa que todas as páginas filhas requerem autenticação."""
        routes = [
            'settings-general',
            'settings-rules',
            'settings-integrations',
            'settings-templates',
            'settings-assistant',
            'settings-pause-classification',
            'settings-users',
        ]
        
        for route_name in routes:
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, 302, f'Route {route_name} should redirect')
            self.assertIn('/login', response.url, f'Route {route_name} should redirect to login')


class SettingsAliasRouteTests(TestCase):
    """Testes para rotas alias de configurações."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
    
    def test_settings_alias_route_works(self):
        """Testa que a rota /settings/ funciona como alias."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('settings'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/settings_hub.html')
    
    def test_configuracoes_route_works(self):
        """Testa que a rota /configuracoes/ funciona."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('settings-hub'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/settings_hub.html')
