"""
Management command para configurar grupos e permissões do sistema.

Uso:
    python manage.py setup_permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction


class Command(BaseCommand):
    help = 'Configura grupos de usuários e suas permissões'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Configurando grupos e permissões...'))
        
        with transaction.atomic():
            # Criar grupos
            self.create_groups()
            
            # Configurar permissões por grupo
            self.setup_operadores()
            self.setup_supervisores()
            self.setup_gestores()
            self.setup_analistas()
            self.setup_administradores()
            self.setup_administradores_sistema()
            
            # Criar permissões customizadas
            self.create_custom_permissions()
        
        self.stdout.write(self.style.SUCCESS('✓ Grupos e permissões configurados com sucesso!'))
        self.print_summary()
    
    def create_groups(self):
        """Cria os grupos de usuários."""
        groups = [
            'Operadores',
            'Supervisores',
            'Gestores',
            'Analistas',
            'Administradores',
            'Administradores de Sistema',
        ]
        
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'  ✓ Grupo criado: {group_name}')
            else:
                self.stdout.write(f'  • Grupo já existe: {group_name}')
    
    def setup_operadores(self):
        """Configura permissões para Operadores."""
        group = Group.objects.get(name='Operadores')
        
        permissions = [
            # Monitoramento - Visualização
            'monitoring.view_agent',
            'monitoring.view_agentevent',
            'monitoring.view_agentworkday',
            'monitoring.view_agentdaystats',
            'monitoring.view_pauseclassification',
            
            # Dashboard
            'monitoring.view_dashboard',
        ]
        
        self.add_permissions_to_group(group, permissions)
        self.stdout.write(f'  ✓ Permissões configuradas para: Operadores')
    
    def setup_supervisores(self):
        """Configura permissões para Supervisores."""
        group = Group.objects.get(name='Supervisores')
        
        permissions = [
            # Tudo de Operadores
            'monitoring.view_agent',
            'monitoring.view_agentevent',
            'monitoring.view_agentworkday',
            'monitoring.view_agentdaystats',
            'monitoring.view_pauseclassification',
            'monitoring.view_dashboard',
            
            # Monitoramento - Edição limitada
            'monitoring.change_pauseclassification',
            
            # Assistente
            'assistant.view_assistantconversation',
            'assistant.view_assistantmessage',
        ]
        
        self.add_permissions_to_group(group, permissions)
        self.stdout.write(f'  ✓ Permissões configuradas para: Supervisores')
    
    def setup_gestores(self):
        """Configura permissões para Gestores."""
        group = Group.objects.get(name='Gestores')
        
        permissions = [
            # Tudo de Supervisores
            'monitoring.view_agent',
            'monitoring.view_agentevent',
            'monitoring.view_agentworkday',
            'monitoring.view_agentdaystats',
            'monitoring.view_pauseclassification',
            'monitoring.view_dashboard',
            'monitoring.change_pauseclassification',
            'assistant.view_assistantconversation',
            'assistant.view_assistantmessage',
            
            # Relatórios
            'reports.view_reports',
            
            # Agentes - Gerenciamento
            'monitoring.change_agent',
            'monitoring.add_agent',
            
            # Assistente - Uso completo
            'assistant.add_assistantconversation',
            'assistant.change_assistantconversation',
        ]
        
        self.add_permissions_to_group(group, permissions)
        self.stdout.write(f'  ✓ Permissões configuradas para: Gestores')
    
    def setup_analistas(self):
        """Configura permissões para Analistas."""
        group = Group.objects.get(name='Analistas')
        
        permissions = [
            # Visualização ampla
            'monitoring.view_agent',
            'monitoring.view_agentevent',
            'monitoring.view_agentworkday',
            'monitoring.view_agentdaystats',
            'monitoring.view_pauseclassification',
            'monitoring.view_dashboard',
            
            # Relatórios
            'reports.view_reports',
            'reports.add_report',
            'reports.change_report',
            
            # Assistente
            'assistant.view_assistantconversation',
            'assistant.add_assistantconversation',
        ]
        
        self.add_permissions_to_group(group, permissions)
        self.stdout.write(f'  ✓ Permissões configuradas para: Analistas')
    
    def setup_administradores(self):
        """Configura permissões para Administradores."""
        group = Group.objects.get(name='Administradores')
        
        permissions = [
            # Configurações
            'core.manage_settings',
            
            # Regras
            'rules.view_systemconfig',
            'rules.add_systemconfig',
            'rules.change_systemconfig',
            'rules.delete_systemconfig',
            
            # Integrações
            'integrations.view_integration',
            'integrations.add_integration',
            'integrations.change_integration',
            'integrations.delete_integration',
            
            # Templates
            'messaging.view_messagetemplate',
            'messaging.add_messagetemplate',
            'messaging.change_messagetemplate',
            'messaging.delete_messagetemplate',
            
            # Monitoramento - Completo
            'monitoring.view_agent',
            'monitoring.add_agent',
            'monitoring.change_agent',
            'monitoring.delete_agent',
            'monitoring.view_pauseclassification',
            'monitoring.add_pauseclassification',
            'monitoring.change_pauseclassification',
            'monitoring.delete_pauseclassification',
            'monitoring.view_dashboard',
            
            # Assistente - Gerenciamento
            'assistant.manage_assistant',
            'assistant.view_assistantconversation',
            'assistant.view_assistantmessage',
            'assistant.view_assistantauditlog',
            
            # Relatórios
            'reports.view_reports',
        ]
        
        self.add_permissions_to_group(group, permissions)
        self.stdout.write(f'  ✓ Permissões configuradas para: Administradores')
    
    def setup_administradores_sistema(self):
        """Configura permissões para Administradores de Sistema."""
        group = Group.objects.get(name='Administradores de Sistema')
        
        permissions = [
            # Tudo de Administradores
            'core.manage_settings',
            'rules.view_systemconfig',
            'rules.add_systemconfig',
            'rules.change_systemconfig',
            'rules.delete_systemconfig',
            'integrations.view_integration',
            'integrations.add_integration',
            'integrations.change_integration',
            'integrations.delete_integration',
            'messaging.view_messagetemplate',
            'messaging.add_messagetemplate',
            'messaging.change_messagetemplate',
            'messaging.delete_messagetemplate',
            'monitoring.view_agent',
            'monitoring.add_agent',
            'monitoring.change_agent',
            'monitoring.delete_agent',
            'monitoring.view_pauseclassification',
            'monitoring.add_pauseclassification',
            'monitoring.change_pauseclassification',
            'monitoring.delete_pauseclassification',
            'monitoring.view_dashboard',
            'assistant.manage_assistant',
            'assistant.view_assistantconversation',
            'assistant.view_assistantmessage',
            'assistant.view_assistantauditlog',
            'reports.view_reports',
            
            # Usuários - Gerenciamento
            'auth.view_user',
            'auth.add_user',
            'auth.change_user',
            'auth.delete_user',
            'auth.view_group',
            'auth.add_group',
            'auth.change_group',
            'auth.delete_group',
        ]
        
        self.add_permissions_to_group(group, permissions)
        self.stdout.write(f'  ✓ Permissões configuradas para: Administradores de Sistema')
    
    def create_custom_permissions(self):
        """Cria permissões customizadas que não existem nos models."""
        custom_permissions = [
            {
                'app_label': 'core',
                'codename': 'manage_settings',
                'name': 'Can manage system settings',
            },
            {
                'app_label': 'monitoring',
                'codename': 'view_dashboard',
                'name': 'Can view dashboard',
            },
            {
                'app_label': 'reports',
                'codename': 'view_reports',
                'name': 'Can view reports',
            },
            {
                'app_label': 'reports',
                'codename': 'add_report',
                'name': 'Can add report',
            },
            {
                'app_label': 'reports',
                'codename': 'change_report',
                'name': 'Can change report',
            },
            {
                'app_label': 'assistant',
                'codename': 'manage_assistant',
                'name': 'Can manage assistant',
            },
        ]
        
        for perm_data in custom_permissions:
            # Obter ou criar ContentType para o app
            content_type, _ = ContentType.objects.get_or_create(
                app_label=perm_data['app_label'],
                model='customperms'  # Model fictício para permissões customizadas
            )
            
            # Criar permissão
            permission, created = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                content_type=content_type,
                defaults={'name': perm_data['name']}
            )
            
            if created:
                self.stdout.write(f'  ✓ Permissão customizada criada: {perm_data["app_label"]}.{perm_data["codename"]}')
    
    def add_permissions_to_group(self, group, permission_codenames):
        """Adiciona lista de permissões a um grupo."""
        for codename in permission_codenames:
            try:
                app_label, perm_codename = codename.split('.')
                permission = Permission.objects.get(
                    codename=perm_codename,
                    content_type__app_label=app_label
                )
                group.permissions.add(permission)
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'    ⚠ Permissão não encontrada: {codename}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'    ✗ Erro ao adicionar {codename}: {str(e)}')
                )
    
    def print_summary(self):
        """Imprime resumo dos grupos criados."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('RESUMO DOS GRUPOS CRIADOS'))
        self.stdout.write('='*60 + '\n')
        
        groups = Group.objects.all().order_by('name')
        for group in groups:
            perm_count = group.permissions.count()
            self.stdout.write(f'  • {group.name}: {perm_count} permissões')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Para adicionar um usuário a um grupo:')
        self.stdout.write('  user.groups.add(Group.objects.get(name="Nome do Grupo"))')
        self.stdout.write('='*60 + '\n')
