"""
Testes para os services de Configurações.

Testa a lógica de negócio dos services que agregam dados
e calculam scores de saúde.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from apps.core.services.settings_service import (
    get_settings_dashboard_data,
    get_settings_health_overview,
    get_settings_alerts,
    build_system_configs_summary,
    build_integrations_summary,
    build_message_templates_summary,
    calculate_config_health,
)
from apps.rules.models import SystemConfig
from apps.integrations.models import Integration
from apps.messaging.models import MessageTemplate
from apps.monitoring.models import Agent, PauseClassification


class SettingsServiceTests(TestCase):
    """Testes para o service principal de configurações."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        # Criar dados de teste
        SystemConfig.objects.create(
            config_key='test.config1',
            config_value='value1'
        )
        SystemConfig.objects.create(
            config_key='test.config2',
            config_value='value2'
        )
        
        Integration.objects.create(
            name='Test Integration',
            channel='EMAIL',
            enabled=True
        )
        
        MessageTemplate.objects.create(
            name='Test Template',
            channel='EMAIL',
            template_type='ALERT',
            active=True
        )
        
        Agent.objects.create(
            nome='Test Agent',
            matricula='12345',
            ativo=True
        )
        
        User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
    
    def test_get_settings_dashboard_data_returns_all_sections(self):
        """Testa que o dashboard retorna todas as seções."""
        data = get_settings_dashboard_data()
        
        # Verificar que todas as seções estão presentes
        self.assertIn('system_configs', data)
        self.assertIn('operational_rules', data)
        self.assertIn('integrations', data)
        self.assertIn('message_templates', data)
        self.assertIn('assistant_config', data)
        self.assertIn('pause_classification', data)
        self.assertIn('user_management', data)
        self.assertIn('appearance', data)
        self.assertIn('recent_changes', data)
    
    def test_get_settings_health_overview_returns_scores(self):
        """Testa que o overview de saúde retorna scores."""
        health = get_settings_health_overview()
        
        self.assertIn('total_score', health)
        self.assertIn('overall_status', health)
        self.assertIn('scores', health)
        
        # Verificar que o score está entre 0 e 100
        self.assertGreaterEqual(health['total_score'], 0)
        self.assertLessEqual(health['total_score'], 100)
        
        # Verificar que o status é válido
        valid_statuses = ['excellent', 'good', 'fair', 'poor']
        self.assertIn(health['overall_status'], valid_statuses)
    
    def test_get_settings_alerts_returns_list(self):
        """Testa que os alertas retornam uma lista."""
        alerts = get_settings_alerts()
        
        self.assertIsInstance(alerts, list)
        
        # Se houver alertas, verificar estrutura
        if alerts:
            alert = alerts[0]
            self.assertIn('severity', alert)
            self.assertIn('title', alert)
            self.assertIn('message', alert)
    
    def test_build_system_configs_summary_with_data(self):
        """Testa resumo de configs com dados."""
        summary = build_system_configs_summary()
        
        self.assertIn('total', summary)
        self.assertIn('categories', summary)
        self.assertIn('status', summary)
        self.assertIn('health', summary)
        
        # Verificar que encontrou as configs criadas
        self.assertGreater(summary['total'], 0)
        self.assertEqual(summary['status'], 'warning')  # < 5 configs
    
    def test_build_integrations_summary_with_data(self):
        """Testa resumo de integrações com dados."""
        summary = build_integrations_summary()
        
        self.assertIn('total', summary)
        self.assertIn('enabled', summary)
        self.assertIn('disabled', summary)
        self.assertIn('status', summary)
        self.assertIn('health_score', summary)
        
        # Verificar dados
        self.assertEqual(summary['total'], 1)
        self.assertEqual(summary['enabled'], 1)
        self.assertEqual(summary['status'], 'active')
        self.assertEqual(summary['health_score'], 100)  # 1/1 = 100%
    
    def test_build_message_templates_summary_with_data(self):
        """Testa resumo de templates com dados."""
        summary = build_message_templates_summary()
        
        self.assertIn('total', summary)
        self.assertIn('active', summary)
        self.assertIn('inactive', summary)
        self.assertIn('status', summary)
        
        # Verificar dados
        self.assertEqual(summary['total'], 1)
        self.assertEqual(summary['active'], 1)
        self.assertEqual(summary['status'], 'active')
    
    def test_calculate_config_health_with_no_configs(self):
        """Testa cálculo de saúde sem configs."""
        stats = {'total': 0, 'categories_count': 0}
        health = calculate_config_health(stats)
        
        self.assertEqual(health, 0)
    
    def test_calculate_config_health_with_configs(self):
        """Testa cálculo de saúde com configs."""
        stats = {'total': 10, 'categories_count': 3}
        health = calculate_config_health(stats)
        
        # Deve retornar um score > 0
        self.assertGreater(health, 0)
        self.assertLessEqual(health, 100)


class SettingsServiceEmptyDataTests(TestCase):
    """Testes para services com dados vazios."""
    
    def test_build_system_configs_summary_empty(self):
        """Testa resumo de configs sem dados."""
        summary = build_system_configs_summary()
        
        self.assertEqual(summary['total'], 0)
        self.assertEqual(summary['status'], 'empty')
        self.assertEqual(summary['health'], 0)
    
    def test_build_integrations_summary_empty(self):
        """Testa resumo de integrações sem dados."""
        summary = build_integrations_summary()
        
        self.assertEqual(summary['total'], 0)
        self.assertEqual(summary['enabled'], 0)
        self.assertEqual(summary['status'], 'empty')
        self.assertEqual(summary['health_score'], 0)
    
    def test_build_message_templates_summary_empty(self):
        """Testa resumo de templates sem dados."""
        summary = build_message_templates_summary()
        
        self.assertEqual(summary['total'], 0)
        self.assertEqual(summary['active'], 0)
        self.assertEqual(summary['status'], 'empty')
