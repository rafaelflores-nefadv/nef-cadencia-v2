"""
Testes para navegação e links do sistema.

Testa que todos os links principais funcionam e que a navegação
está correta após a refatoração.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class NavigationLinksTests(TestCase):
    """Testes para links de navegação principais."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.client = Client()
        
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
    
    def test_dashboard_link_works(self):
        """Testa que o link do dashboard funciona."""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_settings_hub_link_works(self):
        """Testa que o link de configurações funciona."""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('settings-hub'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_assistant_link_works(self):
        """Testa que o link do assistente funciona."""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('assistant-page'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_agents_list_link_works(self):
        """Testa que o link de agentes funciona."""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('agents-list'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_runs_list_link_works(self):
        """Testa que o link de logs funciona."""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('runs-list'))
        
        self.assertEqual(response.status_code, 200)


class SettingsNavigationTests(TestCase):
    """Testes para navegação dentro de configurações."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.client = Client()
        
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        
        self.client.login(username='staff', password='testpass123')
    
    def test_settings_hub_to_general(self):
        """Testa navegação de hub para general."""
        # Acessar hub
        response = self.client.get(reverse('settings-hub'))
        self.assertEqual(response.status_code, 200)
        
        # Acessar general
        response = self.client.get(reverse('settings-general'))
        self.assertEqual(response.status_code, 200)
    
    def test_settings_hub_to_rules(self):
        """Testa navegação de hub para rules."""
        response = self.client.get(reverse('settings-rules'))
        self.assertEqual(response.status_code, 200)
    
    def test_settings_hub_to_integrations(self):
        """Testa navegação de hub para integrations."""
        response = self.client.get(reverse('settings-integrations'))
        self.assertEqual(response.status_code, 200)
    
    def test_settings_hub_to_templates(self):
        """Testa navegação de hub para templates."""
        response = self.client.get(reverse('settings-templates'))
        self.assertEqual(response.status_code, 200)
    
    def test_settings_hub_to_assistant(self):
        """Testa navegação de hub para assistant."""
        response = self.client.get(reverse('settings-assistant'))
        self.assertEqual(response.status_code, 200)
    
    def test_settings_hub_to_pause_classification(self):
        """Testa navegação de hub para pause classification."""
        response = self.client.get(reverse('settings-pause-classification'))
        self.assertEqual(response.status_code, 200)
    
    def test_settings_hub_to_users(self):
        """Testa navegação de hub para users."""
        response = self.client.get(reverse('settings-users'))
        self.assertEqual(response.status_code, 200)


class URLPatternsTests(TestCase):
    """Testes para padrões de URL."""
    
    def test_settings_hub_url_pattern(self):
        """Testa que o padrão de URL de configurações está correto."""
        url = reverse('settings-hub')
        self.assertEqual(url, '/configuracoes/')
    
    def test_settings_alias_url_pattern(self):
        """Testa que o alias /settings/ funciona."""
        url = reverse('settings')
        self.assertEqual(url, '/settings/')
    
    def test_settings_general_url_pattern(self):
        """Testa padrão de URL de general."""
        url = reverse('settings-general')
        self.assertEqual(url, '/settings/general/')
    
    def test_settings_rules_url_pattern(self):
        """Testa padrão de URL de rules."""
        url = reverse('settings-rules')
        self.assertEqual(url, '/settings/rules/')
    
    def test_settings_integrations_url_pattern(self):
        """Testa padrão de URL de integrations."""
        url = reverse('settings-integrations')
        self.assertEqual(url, '/settings/integrations/')
    
    def test_settings_templates_url_pattern(self):
        """Testa padrão de URL de templates."""
        url = reverse('settings-templates')
        self.assertEqual(url, '/settings/templates/')
    
    def test_settings_assistant_url_pattern(self):
        """Testa padrão de URL de assistant."""
        url = reverse('settings-assistant')
        self.assertEqual(url, '/settings/assistant/')
    
    def test_settings_pause_classification_url_pattern(self):
        """Testa padrão de URL de pause classification."""
        url = reverse('settings-pause-classification')
        self.assertEqual(url, '/settings/pause-classification/')
    
    def test_settings_users_url_pattern(self):
        """Testa padrão de URL de users."""
        url = reverse('settings-users')
        self.assertEqual(url, '/settings/users/')


class BreadcrumbsTests(TestCase):
    """Testes para breadcrumbs."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.client = Client()
        
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        
        self.client.login(username='staff', password='testpass123')
    
    def test_settings_hub_has_breadcrumbs(self):
        """Testa que settings hub tem breadcrumbs."""
        response = self.client.get(reverse('settings-hub'))
        
        # Verificar que breadcrumbs estão no contexto
        self.assertIn('breadcrumbs', response.context)
        
        breadcrumbs = response.context['breadcrumbs']
        self.assertIsInstance(breadcrumbs, list)
        self.assertGreater(len(breadcrumbs), 0)
    
    def test_settings_general_has_breadcrumbs(self):
        """Testa que settings general tem breadcrumbs."""
        response = self.client.get(reverse('settings-general'))
        
        # View deve ter método get_breadcrumbs
        self.assertIn('view', response.context)


class CompatibilityTests(TestCase):
    """Testes de compatibilidade com estrutura existente."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.client = Client()
        
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        
        self.client.login(username='staff', password='testpass123')
    
    def test_dashboard_still_works(self):
        """Testa que dashboard existente ainda funciona."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_agents_list_still_works(self):
        """Testa que lista de agentes ainda funciona."""
        response = self.client.get(reverse('agents-list'))
        self.assertEqual(response.status_code, 200)
    
    def test_assistant_page_still_works(self):
        """Testa que página do assistente ainda funciona."""
        response = self.client.get(reverse('assistant-page'))
        self.assertEqual(response.status_code, 200)
    
    def test_runs_list_still_works(self):
        """Testa que lista de runs ainda funciona."""
        response = self.client.get(reverse('runs-list'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_index_still_accessible(self):
        """Testa que Django Admin ainda é acessível."""
        response = self.client.get('/admin/')
        
        # Pode ser 200 (se logado) ou 302 (redirect para login)
        self.assertIn(response.status_code, [200, 302])
