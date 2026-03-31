# Sistema de Permissões e Controle de Acesso

**Data:** 18 de Março de 2026  
**Versão:** 1.0  
**Status:** Implementado ✅

---

## 1. Resumo Executivo

Foi implementado um **sistema completo de permissões e controle de acesso** baseado em grupos e permissões do Django, preparando o sistema para controle granular de acesso por perfil de usuário.

### Objetivos Alcançados
- ✅ 6 grupos de acesso definidos
- ✅ 8 mixins de permissão criados
- ✅ 2 decorators para function-based views
- ✅ 8 helpers de autorização
- ✅ Context processor para menu dinâmico
- ✅ Management command para setup automático
- ✅ Feedback amigável em caso de negação
- ✅ Preparado para multi-setor e workspaces

---

## 2. Grupos de Acesso (Perfis)

### 2.1 Hierarquia de Grupos

```
Administradores de Sistema (Superadmin)
├── Administradores (Admin)
│   ├── Gestores (Manager)
│   │   ├── Supervisores (Supervisor)
│   │   │   └── Operadores (Operator)
│   │   └── Analistas (Analyst)
```

### 2.2 Operadores

**Descrição:** Usuários operacionais com acesso básico ao sistema.

**Permissões:**
- ✅ Visualizar dashboard
- ✅ Visualizar agentes
- ✅ Visualizar eventos de agentes
- ✅ Visualizar estatísticas operacionais
- ✅ Visualizar classificação de pausas
- ❌ Editar configurações
- ❌ Gerenciar integrações
- ❌ Gerenciar usuários

**Casos de uso:**
- Operadores de call center
- Atendentes
- Usuários de visualização

### 2.3 Supervisores

**Descrição:** Supervisores operacionais com permissões de edição limitadas.

**Permissões:**
- ✅ Tudo de Operadores
- ✅ Editar classificação de pausas
- ✅ Visualizar conversas do assistente
- ❌ Gerenciar configurações
- ❌ Gerenciar integrações

**Casos de uso:**
- Supervisores de equipe
- Coordenadores operacionais

### 2.4 Gestores

**Descrição:** Gestores com acesso amplo ao sistema.

**Permissões:**
- ✅ Tudo de Supervisores
- ✅ Gerenciar agentes (adicionar, editar)
- ✅ Visualizar e criar relatórios
- ✅ Usar assistente IA completamente
- ❌ Gerenciar configurações do sistema
- ❌ Gerenciar usuários

**Casos de uso:**
- Gerentes de operação
- Gestores de equipe

### 2.5 Analistas

**Descrição:** Analistas com foco em dados e relatórios.

**Permissões:**
- ✅ Visualizar dashboard e monitoramento
- ✅ Criar e editar relatórios
- ✅ Usar assistente IA
- ✅ Visualizar todas as estatísticas
- ❌ Editar agentes
- ❌ Gerenciar configurações

**Casos de uso:**
- Analistas de dados
- Analistas de qualidade
- BI

### 2.6 Administradores

**Descrição:** Administradores do sistema com controle total de configurações.

**Permissões:**
- ✅ Gerenciar configurações do sistema
- ✅ Gerenciar regras operacionais
- ✅ Gerenciar integrações
- ✅ Gerenciar templates de mensagens
- ✅ Gerenciar classificação de pausas
- ✅ Gerenciar agentes
- ✅ Gerenciar assistente IA
- ✅ Visualizar relatórios
- ❌ Gerenciar usuários do sistema

**Casos de uso:**
- Administradores de sistema
- Responsáveis técnicos

### 2.7 Administradores de Sistema

**Descrição:** Superadministradores com acesso total.

**Permissões:**
- ✅ Tudo de Administradores
- ✅ Gerenciar usuários
- ✅ Gerenciar grupos e permissões
- ✅ Acesso total ao Django Admin

**Casos de uso:**
- Administradores de TI
- Desenvolvedores
- Suporte técnico

---

## 3. Mixins de Permissão

### 3.1 PermissionRequiredMixin (Base)

**Uso genérico para qualquer permissão:**

```python
from apps.core.permissions_advanced import PermissionRequiredMixin

class MyView(PermissionRequiredMixin, View):
    permission_required = 'app.permission_name'
    # ou múltiplas
    permission_required = ['app.perm1', 'app.perm2']
```

### 3.2 DashboardAccessMixin

**Para acesso ao dashboard:**

```python
from apps.core.permissions_advanced import DashboardAccessMixin

class DashboardView(DashboardAccessMixin, TemplateView):
    template_name = 'dashboard.html'
```

**Permite acesso a:**
- Usuários staff
- Usuários com permissão `monitoring.view_dashboard`
- Usuários do grupo `Operadores`

### 3.3 ConfigurationAccessMixin

**Para acesso às configurações:**

```python
from apps.core.permissions_advanced import ConfigurationAccessMixin

class SettingsView(ConfigurationAccessMixin, TemplateView):
    template_name = 'settings.html'
```

**Permite acesso a:**
- Usuários staff
- Usuários com permissão `core.manage_settings`
- Usuários do grupo `Administradores`

### 3.4 IntegrationManagementMixin

**Para gerenciamento de integrações:**

```python
from apps.core.permissions_advanced import IntegrationManagementMixin

class IntegrationView(IntegrationManagementMixin, UpdateView):
    model = Integration
```

### 3.5 RulesManagementMixin

**Para gerenciamento de regras:**

```python
from apps.core.permissions_advanced import RulesManagementMixin

class RulesView(RulesManagementMixin, UpdateView):
    model = SystemConfig
```

### 3.6 UserManagementMixin

**Para gerenciamento de usuários:**

```python
from apps.core.permissions_advanced import UserManagementMixin

class UserView(UserManagementMixin, UpdateView):
    model = User
```

### 3.7 AssistantManagementMixin

**Para gerenciamento do assistente:**

```python
from apps.core.permissions_advanced import AssistantManagementMixin

class AssistantConfigView(AssistantManagementMixin, TemplateView):
    template_name = 'assistant_config.html'
```

### 3.8 ReportsAccessMixin

**Para acesso a relatórios:**

```python
from apps.core.permissions_advanced import ReportsAccessMixin

class ReportsView(ReportsAccessMixin, ListView):
    model = Report
```

### 3.9 MonitoringAccessMixin

**Para acesso ao monitoramento:**

```python
from apps.core.permissions_advanced import MonitoringAccessMixin

class MonitoringView(MonitoringAccessMixin, TemplateView):
    template_name = 'monitoring.html'
```

---

## 4. Decorators para Function-Based Views

### 4.1 permission_required

**Uso genérico:**

```python
from apps.core.permissions_advanced import permission_required

@permission_required('app.permission_name')
def my_view(request):
    return render(request, 'template.html')

# Com múltiplas permissões
@permission_required(['app.perm1', 'app.perm2'])
def my_view(request):
    return render(request, 'template.html')

# Com mensagem customizada
@permission_required(
    'app.permission_name',
    message='Você não pode acessar esta funcionalidade.'
)
def my_view(request):
    return render(request, 'template.html')
```

### 4.2 dashboard_access_required

```python
from apps.core.permissions_advanced import dashboard_access_required

@dashboard_access_required
def dashboard_view(request):
    return render(request, 'dashboard.html')
```

### 4.3 configuration_access_required

```python
from apps.core.permissions_advanced import configuration_access_required

@configuration_access_required
def settings_view(request):
    return render(request, 'settings.html')
```

---

## 5. Helpers de Autorização

### 5.1 Uso em Views

```python
from apps.core.permissions_advanced import (
    user_can_manage_settings,
    user_can_manage_integrations,
)

def my_view(request):
    if user_can_manage_settings(request.user):
        # Lógica para usuários com permissão
        pass
    else:
        # Lógica alternativa
        pass
```

### 5.2 Uso em Templates

```django
{% if can_manage_settings %}
    <a href="{% url 'settings-hub' %}">Configurações</a>
{% endif %}

{% if can_manage_integrations %}
    <a href="{% url 'integration-list' %}">Integrações</a>
{% endif %}
```

### 5.3 Lista Completa de Helpers

```python
user_can_access_dashboard(user) -> bool
user_can_manage_settings(user) -> bool
user_can_manage_integrations(user) -> bool
user_can_manage_rules(user) -> bool
user_can_manage_users(user) -> bool
user_can_manage_assistant(user) -> bool
user_can_view_reports(user) -> bool
user_can_access_monitoring(user) -> bool
```

### 5.4 Resumo de Permissões

```python
from apps.core.permissions_advanced import get_user_permissions_summary

permissions = get_user_permissions_summary(request.user)
# Retorna:
{
    'can_access_dashboard': True,
    'can_manage_settings': False,
    'can_manage_integrations': False,
    'can_manage_rules': False,
    'can_manage_users': False,
    'can_manage_assistant': False,
    'can_view_reports': True,
    'can_access_monitoring': True,
    'is_staff': False,
    'is_superuser': False,
}
```

---

## 6. Context Processor para Menu Dinâmico

### 6.1 Configuração

O context processor `user_permissions` já está configurado e adiciona automaticamente as permissões do usuário ao contexto de todos os templates.

### 6.2 Uso no Menu Lateral

```django
<!-- templates/partials/sidebar.html -->

{% if can_access_dashboard %}
<a href="{% url 'dashboard' %}" class="menu-item">
    Dashboard
</a>
{% endif %}

{% if can_manage_settings %}
<a href="{% url 'settings-hub' %}" class="menu-item">
    Configurações
</a>
{% endif %}

{% if can_manage_integrations %}
<a href="{% url 'integration-list' %}" class="menu-item">
    Integrações
</a>
{% endif %}

{% if can_view_reports %}
<a href="{% url 'reports-list' %}" class="menu-item">
    Relatórios
</a>
{% endif %}
```

### 6.3 Esconder Seções Completas

```django
{% if can_manage_settings or can_manage_integrations or can_manage_rules %}
<div class="menu-section">
    <h3>Administração</h3>
    
    {% if can_manage_settings %}
    <a href="{% url 'settings-hub' %}">Configurações</a>
    {% endif %}
    
    {% if can_manage_integrations %}
    <a href="{% url 'integration-list' %}">Integrações</a>
    {% endif %}
    
    {% if can_manage_rules %}
    <a href="{% url 'config-list' %}">Regras</a>
    {% endif %}
</div>
{% endif %}
```

---

## 7. Setup Inicial do Sistema

### 7.1 Executar Management Command

```bash
python manage.py setup_permissions
```

**Saída esperada:**
```
Configurando grupos e permissões...
  ✓ Grupo criado: Operadores
  ✓ Grupo criado: Supervisores
  ✓ Grupo criado: Gestores
  ✓ Grupo criado: Analistas
  ✓ Grupo criado: Administradores
  ✓ Grupo criado: Administradores de Sistema
  ✓ Permissões configuradas para: Operadores
  ✓ Permissões configuradas para: Supervisores
  ✓ Permissões configuradas para: Gestores
  ✓ Permissões configuradas para: Analistas
  ✓ Permissões configuradas para: Administradores
  ✓ Permissões configuradas para: Administradores de Sistema
  ✓ Permissão customizada criada: core.manage_settings
  ✓ Permissão customizada criada: monitoring.view_dashboard
  ✓ Grupos e permissões configurados com sucesso!

============================================================
RESUMO DOS GRUPOS CRIADOS
============================================================

  • Administradores: 45 permissões
  • Administradores de Sistema: 53 permissões
  • Analistas: 12 permissões
  • Gestores: 18 permissões
  • Operadores: 6 permissões
  • Supervisores: 9 permissões

============================================================
```

---

## 8. Como Cadastrar Novos Perfis

### 8.1 Adicionar Usuário a um Grupo

**Via Django Admin:**
1. Acessar `/admin/auth/user/`
2. Selecionar o usuário
3. Na seção "Permissions", adicionar aos grupos desejados
4. Salvar

**Via Python Shell:**
```python
from django.contrib.auth.models import User, Group

# Obter usuário
user = User.objects.get(username='joao.silva')

# Adicionar a um grupo
grupo_operadores = Group.objects.get(name='Operadores')
user.groups.add(grupo_operadores)

# Adicionar a múltiplos grupos
user.groups.add(
    Group.objects.get(name='Operadores'),
    Group.objects.get(name='Analistas')
)

# Remover de um grupo
user.groups.remove(grupo_operadores)

# Limpar todos os grupos
user.groups.clear()
```

**Via Management Command (criar custom):**
```python
# apps/core/management/commands/assign_user_group.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('group', type=str)
    
    def handle(self, *args, **options):
        user = User.objects.get(username=options['username'])
        group = Group.objects.get(name=options['group'])
        user.groups.add(group)
        self.stdout.write(f'✓ {user.username} adicionado ao grupo {group.name}')
```

```bash
python manage.py assign_user_group joao.silva Operadores
```

### 8.2 Criar Novo Grupo Customizado

```python
from django.contrib.auth.models import Group, Permission

# Criar grupo
grupo_custom = Group.objects.create(name='Auditores')

# Adicionar permissões específicas
permissoes = [
    Permission.objects.get(codename='view_agent'),
    Permission.objects.get(codename='view_agentevent'),
    Permission.objects.get(codename='view_assistantauditlog'),
]

grupo_custom.permissions.set(permissoes)
```

### 8.3 Criar Permissão Customizada

```python
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# Criar ContentType para o app
content_type = ContentType.objects.get_or_create(
    app_label='meu_app',
    model='customperms'
)[0]

# Criar permissão
permission = Permission.objects.create(
    codename='can_export_data',
    name='Can export data',
    content_type=content_type
)
```

---

## 9. Como Aplicar Permissões nas Views

### 9.1 Class-Based Views

**Opção 1: Usar Mixin Específico**
```python
from apps.core.permissions_advanced import ConfigurationAccessMixin

class MyView(ConfigurationAccessMixin, TemplateView):
    template_name = 'my_template.html'
```

**Opção 2: Usar Mixin Genérico**
```python
from apps.core.permissions_advanced import PermissionRequiredMixin

class MyView(PermissionRequiredMixin, TemplateView):
    permission_required = 'app.my_permission'
    template_name = 'my_template.html'
```

**Opção 3: Múltiplas Permissões**
```python
class MyView(PermissionRequiredMixin, TemplateView):
    permission_required = [
        'app.permission1',
        'app.permission2',
    ]
    template_name = 'my_template.html'
```

**Opção 4: Customizar Mensagem e Redirect**
```python
class MyView(PermissionRequiredMixin, TemplateView):
    permission_required = 'app.my_permission'
    permission_denied_message = 'Acesso negado para esta funcionalidade.'
    redirect_url = reverse_lazy('home')
    template_name = 'my_template.html'
```

### 9.2 Function-Based Views

**Opção 1: Usar Decorator Específico**
```python
from apps.core.permissions_advanced import dashboard_access_required

@dashboard_access_required
def my_view(request):
    return render(request, 'template.html')
```

**Opção 2: Usar Decorator Genérico**
```python
from apps.core.permissions_advanced import permission_required

@permission_required('app.my_permission')
def my_view(request):
    return render(request, 'template.html')
```

**Opção 3: Verificação Manual**
```python
from apps.core.permissions_advanced import user_can_manage_settings
from django.contrib import messages
from django.shortcuts import redirect

def my_view(request):
    if not user_can_manage_settings(request.user):
        messages.error(request, 'Você não tem permissão.')
        return redirect('dashboard')
    
    # Lógica da view
    return render(request, 'template.html')
```

### 9.3 Verificação Condicional

```python
def my_view(request):
    context = {}
    
    # Mostrar seção apenas se tiver permissão
    if user_can_manage_integrations(request.user):
        context['integrations'] = Integration.objects.all()
    
    # Funcionalidade diferente por permissão
    if request.user.is_superuser:
        context['all_data'] = get_all_data()
    elif user_can_view_reports(request.user):
        context['all_data'] = get_limited_data()
    
    return render(request, 'template.html', context)
```

---

## 10. Feedback Amigável de Negação

### 10.1 Mensagens Automáticas

Todos os mixins já incluem mensagens amigáveis:

```python
class ConfigurationAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    permission_denied_message = 'Você não tem permissão para gerenciar configurações.'
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)
```

### 10.2 Customizar Mensagens

```python
class MyView(PermissionRequiredMixin, TemplateView):
    permission_required = 'app.my_permission'
    permission_denied_message = 'Esta funcionalidade requer permissão especial. Contate o administrador.'
```

### 10.3 Página de Erro Customizada

```python
# views.py
class AccessDeniedView(TemplateView):
    template_name = 'errors/access_denied.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['required_permission'] = self.request.GET.get('perm', 'desconhecida')
        return context

# urls.py
path('access-denied/', AccessDeniedView.as_view(), name='access-denied'),

# Em um mixin customizado
def handle_no_permission(self):
    return redirect(f'/access-denied/?perm={self.permission_required}')
```

---

## 11. Preparação para Multi-Setor e Workspaces

### 11.1 Estrutura Futura

O sistema está preparado para adicionar:

**Modelo de Workspace:**
```python
class Workspace(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

class WorkspaceMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)  # 'admin', 'member', 'viewer'
```

**Mixin para Workspace:**
```python
class WorkspaceAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        workspace_slug = self.kwargs.get('workspace_slug')
        workspace = Workspace.objects.get(slug=workspace_slug)
        return WorkspaceMembership.objects.filter(
            user=self.request.user,
            workspace=workspace
        ).exists()
```

### 11.2 Permissões por Setor

```python
class Setor(models.Model):
    name = models.CharField(max_length=100)

class SetorPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=False)
    can_manage = models.BooleanField(default=False)
```

---

## 12. Exemplos Práticos

### 12.1 Proteger View de Configurações

```python
from apps.core.permissions_advanced import ConfigurationAccessMixin
from apps.core.views_settings import SettingsHubView

class SettingsHubView(ConfigurationAccessMixin, TemplateView):
    template_name = 'core/settings_hub.html'
    page_title = 'Configurações'
```

### 12.2 Proteger View de Integrações

```python
from apps.core.permissions_advanced import IntegrationManagementMixin

class IntegrationListView(IntegrationManagementMixin, ListView):
    model = Integration
    template_name = 'integrations/list.html'
```

### 12.3 Menu Dinâmico Completo

```django
<!-- sidebar.html -->
<nav>
    {% if can_access_dashboard %}
    <a href="{% url 'dashboard' %}">Dashboard</a>
    {% endif %}
    
    {% if can_access_monitoring %}
    <a href="{% url 'agents-list' %}">Agentes</a>
    {% endif %}
    
    {% if can_manage_settings or can_manage_integrations %}
    <div class="menu-section">
        <h3>Administração</h3>
        
        {% if can_manage_settings %}
        <a href="{% url 'settings-hub' %}">Configurações</a>
        {% endif %}
        
        {% if can_manage_integrations %}
        <a href="{% url 'integration-list' %}">Integrações</a>
        {% endif %}
    </div>
    {% endif %}
    
    {% if can_view_reports %}
    <a href="{% url 'reports-list' %}">Relatórios</a>
    {% endif %}
</nav>
```

---

## 13. Checklist de Implementação

### 13.1 Para Novas Views

- [ ] Escolher mixin apropriado ou usar `PermissionRequiredMixin`
- [ ] Definir `permission_required` se usar mixin genérico
- [ ] Customizar `permission_denied_message` se necessário
- [ ] Testar acesso com diferentes perfis de usuário

### 13.2 Para Novos Módulos

- [ ] Definir permissões necessárias
- [ ] Criar mixin específico se necessário
- [ ] Adicionar permissões ao management command
- [ ] Atualizar context processor se necessário
- [ ] Adicionar itens ao menu com verificação de permissão

### 13.3 Para Novos Grupos

- [ ] Definir nome e descrição do grupo
- [ ] Listar permissões necessárias
- [ ] Adicionar ao management command `setup_permissions`
- [ ] Executar comando para criar grupo
- [ ] Documentar casos de uso

---

## 14. Troubleshooting

### 14.1 Usuário não consegue acessar página

**Verificar:**
1. Usuário está autenticado?
2. Usuário pertence ao grupo correto?
3. Grupo tem as permissões necessárias?
4. Permissões foram aplicadas após adicionar ao grupo?

**Solução:**
```python
# Verificar grupos do usuário
user.groups.all()

# Verificar permissões do usuário
user.get_all_permissions()

# Verificar permissão específica
user.has_perm('app.permission_name')
```

### 14.2 Menu não esconde itens

**Verificar:**
1. Context processor está configurado em settings.py?
2. Template está usando as variáveis corretas?
3. Cache do template foi limpo?

**Solução:**
```python
# settings.py
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ...
                'apps.core.context_processors.user_permissions',
            ],
        },
    },
]
```

### 14.3 Permissão customizada não funciona

**Verificar:**
1. Permissão foi criada no banco?
2. ContentType está correto?
3. Grupo tem a permissão?

**Solução:**
```python
# Verificar se permissão existe
Permission.objects.filter(codename='my_permission')

# Recriar permissão se necessário
python manage.py setup_permissions
```

---

## 15. Conclusão

O sistema de permissões está **completo e pronto para uso**, oferecendo:

✅ **6 Grupos de Acesso** - Hierarquia clara de perfis  
✅ **8 Mixins** - Reutilizáveis em class-based views  
✅ **2 Decorators** - Para function-based views  
✅ **8 Helpers** - Verificação programática  
✅ **Context Processor** - Menu dinâmico automático  
✅ **Management Command** - Setup automático  
✅ **Feedback Amigável** - Mensagens de erro claras  
✅ **Preparado para Expansão** - Multi-setor e workspaces  

O sistema está pronto para controlar acesso granular por perfil de usuário! 🔒

---

**Implementação concluída em 18 de Março de 2026**  
**Sistema de permissões enterprise-grade implementado!**
