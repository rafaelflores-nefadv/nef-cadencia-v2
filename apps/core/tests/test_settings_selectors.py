"""
Testes para os selectors de Configurações.

Testa as queries ORM que buscam dados do banco.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.selectors_settings import (
    get_system_configs_stats,
    get_integrations_stats,
    get_message_templates_stats,
    get_pause_classification_stats,
    get_assistant_stats,
    get_users_stats,
    get_operational_rules_stats,
    get_recent_config_changes,
)
from apps.rules.models import SystemConfig
from apps.integrations.models import Integration
from apps.messaging.models import MessageTemplate
from apps.monitoring.models import Agent, PauseClassification
from apps.assistant.models import AssistantConversation


User = get_user_model()


class SettingsSelectorsTests(TestCase):
    """Testes para os selectors de configurações."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        # Criar dados de teste
        SystemConfig.objects.create(
            config_key='operational.threshold',
            config_value='10'
        )
        SystemConfig.objects.create(
            config_key='assistant.model',
            config_value='gpt-4'
        )
        SystemConfig.objects.create(
            config_key='general.timeout',
            config_value='30'
        )
        
        Integration.objects.create(
            name='Email Integration',
            channel='EMAIL',
            enabled=True
        )
        Integration.objects.create(
            name='SMS Integration',
            channel='SMS',
            enabled=False
        )
        
        MessageTemplate.objects.create(
            name='Alert Template',
            channel='EMAIL',
            template_type='ALERT',
            active=True
        )
        MessageTemplate.objects.create(
            name='Notification Template',
            channel='SMS',
            template_type='NOTIFICATION',
            active=False
        )
        
        PauseClassification.objects.create(
            source='',
            pause_name='Test Pause',
            category='LEGAL',
            is_active=True
        )
        
        User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True,
            is_active=True
        )
        User.objects.create_user(
            username='regularuser',
            password='testpass123',
            is_staff=False,
            is_active=True
        )
        
        Agent.objects.create(
            cd_operador=12345,
            nm_agente='Test Agent',
            ativo=True
        )
    
    def test_get_system_configs_stats(self):
        """Testa estatísticas de configurações do sistema."""
        stats = get_system_configs_stats()
        
        self.assertIn('total', stats)
        self.assertIn('categories', stats)
        self.assertIn('categories_count', stats)
        self.assertIn('last_updated', stats)
        
        # Verificar dados
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['categories_count'], 3)  # operational, assistant, general
        self.assertIn('operational', stats['categories'])
        self.assertIn('assistant', stats['categories'])
        self.assertIn('general', stats['categories'])
    
    def test_get_integrations_stats(self):
        """Testa estatísticas de integrações."""
        stats = get_integrations_stats()
        
        self.assertIn('total', stats)
        self.assertIn('enabled', stats)
        self.assertIn('disabled', stats)
        self.assertIn('by_channel', stats)
        
        # Verificar dados
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['enabled'], 1)
        self.assertEqual(stats['disabled'], 1)
        self.assertIn('EMAIL', stats['by_channel'])
        self.assertIn('SMS', stats['by_channel'])
    
    def test_get_message_templates_stats(self):
        """Testa estatísticas de templates de mensagens."""
        stats = get_message_templates_stats()
        
        self.assertIn('total', stats)
        self.assertIn('active', stats)
        self.assertIn('inactive', stats)
        self.assertIn('by_channel', stats)
        self.assertIn('by_type', stats)
        
        # Verificar dados
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['active'], 1)
        self.assertEqual(stats['inactive'], 1)
    
    def test_get_pause_classification_stats(self):
        """Testa estatísticas de classificação de pausas."""
        stats = get_pause_classification_stats()
        
        self.assertIn('total', stats)
        self.assertIn('active', stats)
        self.assertIn('inactive', stats)
        self.assertIn('by_category', stats)
        
        # Verificar dados
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['active'], 1)
        self.assertIn('LEGAL', stats['by_category'])
    
    def test_get_assistant_stats(self):
        """Testa estatísticas do assistente."""
        stats = get_assistant_stats()
        
        self.assertIn('total_conversations', stats)
        self.assertIn('active_conversations', stats)
        self.assertIn('total_messages', stats)
        self.assertIn('recent_conversations', stats)
        self.assertIn('configs', stats)
        
        # Verificar que configs do assistente foram encontradas
        self.assertEqual(stats['configs'], 1)  # assistant.model
    
    def test_get_users_stats(self):
        """Testa estatísticas de usuários."""
        stats = get_users_stats()
        
        self.assertIn('total_users', stats)
        self.assertIn('active_users', stats)
        self.assertIn('staff_users', stats)
        self.assertIn('superusers', stats)
        self.assertIn('total_agents', stats)
        self.assertIn('active_agents', stats)
        
        # Verificar dados
        self.assertEqual(stats['total_users'], 2)
        self.assertEqual(stats['active_users'], 2)
        self.assertEqual(stats['staff_users'], 1)
        self.assertEqual(stats['total_agents'], 1)
        self.assertEqual(stats['active_agents'], 1)
    
    def test_get_operational_rules_stats(self):
        """Testa estatísticas de regras operacionais."""
        stats = get_operational_rules_stats()
        
        self.assertIn('total', stats)
        self.assertIn('by_prefix', stats)
        
        # Verificar que encontrou a config operational
        self.assertEqual(stats['total'], 1)
        self.assertIn('operational', stats['by_prefix'])
    
    def test_get_recent_config_changes(self):
        """Testa busca de alterações recentes."""
        changes = get_recent_config_changes(limit=5)
        
        # Deve retornar um QuerySet
        self.assertEqual(len(changes), 3)
        
        # Verificar que está ordenado por updated_at
        if len(changes) > 1:
            self.assertGreaterEqual(
                changes[0].updated_at,
                changes[1].updated_at
            )


class SettingsSelectorsEmptyDataTests(TestCase):
    """Testes para selectors com dados vazios."""
    
    def test_get_system_configs_stats_empty(self):
        """Testa estatísticas sem configs."""
        stats = get_system_configs_stats()
        
        self.assertEqual(stats['total'], 0)
        self.assertEqual(stats['categories_count'], 0)
        self.assertEqual(stats['categories'], {})
    
    def test_get_integrations_stats_empty(self):
        """Testa estatísticas sem integrações."""
        stats = get_integrations_stats()
        
        self.assertEqual(stats['total'], 0)
        self.assertEqual(stats['enabled'], 0)
        self.assertEqual(stats['disabled'], 0)
    
    def test_get_message_templates_stats_empty(self):
        """Testa estatísticas sem templates."""
        stats = get_message_templates_stats()
        
        self.assertEqual(stats['total'], 0)
        self.assertEqual(stats['active'], 0)
        self.assertEqual(stats['inactive'], 0)
