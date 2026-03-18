# Proposta de Nova Organização de Pastas

**Data:** 18 de Março de 2026  
**Versão:** 1.0  
**Status:** Proposta sem implementação

---

## 1. Estrutura Atual vs. Proposta

### 1.1 Estrutura Atual (Exemplo: `monitoring`)

```
apps/monitoring/
├── __init__.py
├── models.py                    # 481 linhas
├── views.py                     # 2368 linhas ❌
├── admin.py                     # 100 linhas
├── urls.py
├── apps.py
├── guards.py
├── utils.py
├── services/                    # ✅ Já existe
│   ├── __init__.py
│   ├── dashboard_period_filter.py
│   ├── day_stats_service.py
│   ├── legacy_sync_service.py
│   ├── lh_import_utils.py
│   ├── pause_classification.py
│   └── risk_scoring.py
├── management/commands/         # ✅ Já existe
│   └── [10 commands]
├── migrations/
├── tests.py                     # 50889 linhas ❌
├── tests_pause_classification.py
├── tests_pause_classification_ui.py
├── tests_period_filter.py
├── tests_raw_protection.py
└── tests_utils.py
```

### 1.2 Estrutura Proposta (Exemplo: `monitoring`)

```
apps/monitoring/
├── __init__.py
├── models.py                    # Apenas models
├── admin.py                     # Admin simplificado
├── urls.py                      # Rotas
├── apps.py                      # Config do app
│
├── views/                       # ✨ NOVO - Views organizadas
│   ├── __init__.py
│   ├── dashboard_views.py       # Dashboards (< 300 linhas)
│   ├── agent_views.py           # Agentes
│   ├── job_views.py             # Jobs
│   ├── pause_views.py           # Pausas
│   └── config_views.py          # Configurações
│
├── forms.py                     # ✨ NOVO - Formulários
├── permissions.py               # ✨ NOVO - Permissões
├── selectors.py                 # ✨ NOVO - Queries
├── validators.py                # ✨ NOVO - Validações
├── serializers.py               # ✨ NOVO - Formatação
│
├── services/                    # ✅ Já existe - Expandir
│   ├── __init__.py
│   ├── agent_service.py         # ✨ NOVO
│   ├── metrics_service.py       # ✨ NOVO - Extrair de views
│   ├── alerts_service.py        # ✨ NOVO - Extrair de views
│   ├── ranking_service.py       # ✨ NOVO - Extrair de views
│   ├── dashboard_period_filter.py
│   ├── day_stats_service.py
│   ├── legacy_sync_service.py
│   ├── lh_import_utils.py
│   ├── pause_classification.py
│   └── risk_scoring.py
│
├── management/commands/         # ✅ Manter
│   └── [commands existentes]
│
├── migrations/                  # ✅ Manter
│
├── tests/                       # ✨ NOVO - Testes organizados
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_forms.py
│   ├── test_selectors.py
│   ├── test_permissions.py
│   ├── test_services/
│   │   ├── test_agent_service.py
│   │   ├── test_metrics_service.py
│   │   ├── test_alerts_service.py
│   │   ├── test_day_stats_service.py
│   │   ├── test_pause_classification.py
│   │   └── test_risk_scoring.py
│   └── fixtures/
│       └── test_data.json
│
├── templates/monitoring/        # ✅ Manter (fora do app)
└── static/monitoring/           # Se necessário
```

---

## 2. Detalhamento por App

### 2.1 App `monitoring` (Prioritário)

#### Arquivos a Criar

**`views/dashboard_views.py`** (extrair de `views.py`)
```python
# DashboardView e variações
# Máximo 300 linhas
# Apenas orquestração
```

**`views/agent_views.py`**
```python
# AgentListView, AgentDetailView
# Formulários de cadastro/edição
```

**`views/job_views.py`**
```python
# JobRunListView, JobRunDetailView
```

**`views/pause_views.py`**
```python
# PauseClassificationConfigView
```

**`views/config_views.py`** (novo)
```python
# Views para configurações que estão no admin
```

**`forms.py`**
```python
class DashboardFilterForm(forms.Form):
    data_ref = forms.DateField(...)
    period_type = forms.ChoiceField(...)
    # ...

class PauseClassificationForm(forms.ModelForm):
    class Meta:
        model = PauseClassification
        # ...

class AgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        # ...
```

**`permissions.py`**
```python
from django.contrib.auth.mixins import PermissionRequiredMixin

class CanViewDashboard(PermissionRequiredMixin):
    permission_required = 'monitoring.view_dashboard'

class CanManageAgents(PermissionRequiredMixin):
    permission_required = 'monitoring.change_agent'

class CanRebuildStats(PermissionRequiredMixin):
    permission_required = 'monitoring.rebuild_stats'
    
    def test_func(self):
        return self.request.user.is_staff
```

**`selectors.py`**
```python
def get_active_agents():
    """Retorna agentes ativos."""
    return Agent.objects.filter(ativo=True)

def get_events_for_period(start_date, end_date, source=None):
    """Retorna eventos para um período."""
    qs = AgentEvent.objects.filter(
        dt_inicio__gte=start_date,
        dt_inicio__lt=end_date
    )
    if source:
        qs = qs.filter(source=source)
    return qs.select_related('agent')

def get_agent_metrics_for_day(date, agent_ids=None):
    """Retorna métricas agregadas por agente."""
    # Queries complexas aqui
    pass
```

**`validators.py`**
```python
from django.core.exceptions import ValidationError

def validate_operator_code(value):
    """Valida código de operador."""
    if value <= 0:
        raise ValidationError('Código deve ser positivo')

def validate_date_range(start_date, end_date):
    """Valida range de datas."""
    if start_date > end_date:
        raise ValidationError('Data inicial deve ser menor que final')
```

**`serializers.py`**
```python
def serialize_agent_metric(metric_dict):
    """Formata métrica de agente para template."""
    return {
        'cd_operador': metric_dict['cd_operador'],
        'nome': metric_dict['nm_agente'],
        'pausas': metric_dict['qtd_pausas'],
        'tempo_pausas': format_seconds_hhmm(metric_dict['tempo_pausas_seg']),
        # ...
    }

def serialize_dashboard_context(raw_data):
    """Prepara dados para dashboard."""
    # Formatação complexa aqui
    pass
```

**`services/metrics_service.py`** (extrair de views)
```python
def calculate_operator_metrics(events_qs, workday_qs, stats_qs):
    """Calcula métricas de operadores."""
    # Lógica extraída de DashboardView._build_operator_metrics
    pass

def calculate_operational_score(taxa_ocupacao_pct, alert_totals):
    """Calcula score operacional."""
    # Lógica extraída de DashboardView._calculate_operational_score
    pass
```

**`services/alerts_service.py`** (extrair de views)
```python
def build_operational_alerts(operator_metrics, config):
    """Gera alertas operacionais."""
    # Lógica extraída de DashboardView._build_operational_alerts
    pass
```

**`services/ranking_service.py`** (extrair de views)
```python
def build_pause_rankings(operator_metrics):
    """Gera rankings de pausas."""
    # Lógica extraída de DashboardView._build_pause_rankings
    pass

def build_productivity_ranking(operator_metrics):
    """Gera ranking de produtividade."""
    pass
```

**`services/agent_service.py`** (novo)
```python
def create_agent(data):
    """Cria novo agente."""
    pass

def update_agent(agent_id, data):
    """Atualiza agente."""
    pass

def deactivate_agent(agent_id):
    """Desativa agente."""
    pass
```

#### Arquivos a Refatorar

**`views.py`** → **`views/__init__.py`**
- Importar e re-exportar views dos módulos
- Manter compatibilidade com imports existentes

**`tests.py`** → **`tests/`**
- Dividir arquivo gigante em múltiplos arquivos
- Organizar por tipo de teste

---

### 2.2 App `rules` (Prioritário)

#### Estrutura Proposta

```
apps/rules/
├── __init__.py
├── models.py
├── admin.py                     # Simplificar
├── urls.py                      # ✨ NOVO
├── apps.py
│
├── views.py                     # ✨ NOVO
├── forms.py                     # ✨ NOVO
├── permissions.py               # ✨ NOVO
├── selectors.py                 # ✨ NOVO
├── validators.py                # ✨ NOVO
│
├── services/
│   ├── __init__.py
│   └── system_config.py         # ✅ Já existe
│
├── tests/
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_forms.py
│   └── test_services/
│       └── test_system_config_service.py
│
└── templates/rules/             # ✨ NOVO
    ├── config_list.html
    └── config_edit.html
```

#### Arquivos a Criar

**`urls.py`**
```python
from django.urls import path
from .views import ConfigListView, ConfigEditView

urlpatterns = [
    path('configuracoes', ConfigListView.as_view(), name='config-list'),
    path('configuracoes/<str:key>', ConfigEditView.as_view(), name='config-edit'),
]
```

**`views.py`**
```python
class ConfigListView(LoginRequiredMixin, CanManageConfigs, ListView):
    model = SystemConfig
    template_name = 'rules/config_list.html'
    # ...

class ConfigEditView(LoginRequiredMixin, CanManageConfigs, UpdateView):
    model = SystemConfig
    form_class = SystemConfigForm
    template_name = 'rules/config_edit.html'
    # ...
```

**`forms.py`**
```python
class SystemConfigForm(forms.ModelForm):
    class Meta:
        model = SystemConfig
        fields = ['config_value', 'description']
    
    def clean_config_value(self):
        # Validação baseada em value_type
        pass
```

**`permissions.py`**
```python
class CanManageConfigs(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or \
               self.request.user.has_perm('rules.change_systemconfig')
```

**`selectors.py`**
```python
def get_configs_by_category():
    """Retorna configs agrupadas por categoria."""
    pass

def get_config_history(config_key):
    """Retorna histórico de alterações."""
    pass
```

**`validators.py`**
```python
def validate_config_value(value, value_type):
    """Valida valor baseado no tipo."""
    if value_type == 'int':
        try:
            int(value)
        except ValueError:
            raise ValidationError('Valor deve ser inteiro')
    # ...
```

---

### 2.3 App `messaging` (Média Prioridade)

#### Estrutura Proposta

```
apps/messaging/
├── __init__.py
├── models.py
├── admin.py                     # Simplificar
├── urls.py                      # ✨ NOVO
├── apps.py
├── choices.py                   # ✅ Já existe
│
├── views.py                     # ✨ NOVO
├── forms.py                     # ✨ NOVO
├── permissions.py               # ✨ NOVO
├── selectors.py                 # ✨ NOVO
│
├── services/                    # ✨ NOVO
│   ├── __init__.py
│   ├── email_service.py
│   ├── sms_service.py
│   └── template_service.py
│
├── tests/
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_forms.py
│   └── test_services/
│
└── templates/messaging/         # ✨ NOVO
    ├── template_list.html
    ├── template_edit.html
    └── template_preview.html
```

#### Arquivos a Criar

**`urls.py`**
```python
urlpatterns = [
    path('mensagens', TemplateListView.as_view(), name='template-list'),
    path('mensagens/<int:pk>', TemplateEditView.as_view(), name='template-edit'),
    path('mensagens/<int:pk>/preview', TemplatePreviewView.as_view(), name='template-preview'),
]
```

**`services/email_service.py`**
```python
def send_email(recipient, template, context):
    """Envia email usando template."""
    pass
```

**`services/template_service.py`**
```python
def render_template(template, context):
    """Renderiza template com contexto."""
    pass

def get_active_template(template_type, channel):
    """Retorna template ativo."""
    pass
```

---

### 2.4 App `integrations` (Média Prioridade)

#### Estrutura Proposta

```
apps/integrations/
├── __init__.py
├── models.py
├── admin.py                     # Simplificar
├── urls.py                      # ✨ NOVO
├── apps.py
│
├── views.py                     # ✨ NOVO
├── forms.py                     # ✨ NOVO
├── permissions.py               # ✨ NOVO
├── selectors.py                 # ✨ NOVO
│
├── services/                    # ✨ NOVO
│   ├── __init__.py
│   ├── base_integration.py
│   ├── email_integration.py
│   └── sms_integration.py
│
├── tests/
│   └── test_services/
│
└── templates/integrations/      # ✨ NOVO
    ├── integration_list.html
    ├── integration_edit.html
    └── integration_test.html
```

---

### 2.5 App `assistant` (Baixa Prioridade - Já Bem Estruturado)

#### Melhorias Sugeridas

```
apps/assistant/
├── __init__.py
├── models.py                    # ✅ OK
├── admin.py                     # ✅ OK
├── urls.py                      # ✅ OK
├── apps.py
├── observability.py             # ✅ OK
│
├── views.py                     # Pode dividir se crescer
├── forms.py                     # ✨ NOVO - Para preferências
├── permissions.py               # ✨ NOVO - Formalizar
├── selectors.py                 # ✨ NOVO - Queries de conversas
│
├── services/                    # ✅ Excelente!
│   └── [20 arquivos]
│
├── tests/                       # ✅ Já organizado!
│   └── [14 arquivos]
│
└── templates/assistant/         # ✅ OK
```

**Arquivos a Criar:**

**`forms.py`**
```python
class UserPreferenceForm(forms.ModelForm):
    class Meta:
        model = AssistantUserPreference
        fields = ['max_saved_conversations']
```

**`permissions.py`**
```python
class CanUseAssistant(PermissionRequiredMixin):
    permission_required = 'assistant.use_assistant'

class CanManageConversations(PermissionRequiredMixin):
    permission_required = 'assistant.manage_conversations'
```

**`selectors.py`**
```python
def get_user_conversations(user, status='active'):
    """Retorna conversas do usuário."""
    return AssistantConversation.objects.filter(
        created_by=user,
        status=status
    ).prefetch_related('messages')

def get_conversation_with_messages(conversation_id):
    """Retorna conversa com mensagens."""
    pass
```

---

### 2.6 App `accounts` (Baixa Prioridade)

#### Estrutura Proposta

```
apps/accounts/
├── __init__.py
├── models.py                    # ✨ NOVO - User profile
├── admin.py
├── urls.py                      # Expandir
├── apps.py
├── context_processors.py        # ✅ Já existe
│
├── views.py                     # ✨ NOVO - Perfil, senha
├── forms.py                     # ✨ NOVO - Login, perfil
├── permissions.py               # ✨ NOVO
│
├── templatetags/                # ✅ Já existe
│   └── admin_menu.py
│
├── tests/
│   └── test_views.py
│
└── templates/accounts/          # Expandir
    ├── login.html               # ✅ Já existe
    ├── profile.html             # ✨ NOVO
    └── change_password.html     # ✨ NOVO
```

---

### 2.7 App `reports` (Baixa Prioridade - Implementar ou Remover)

#### Opção 1: Implementar

```
apps/reports/
├── __init__.py
├── models.py                    # Report configs
├── admin.py
├── urls.py
├── apps.py
│
├── views.py
├── forms.py
├── permissions.py
│
├── services/
│   ├── report_generator.py
│   ├── pdf_service.py
│   └── excel_service.py
│
├── tests/
│
└── templates/reports/
    ├── report_list.html
    └── report_view.html
```

#### Opção 2: Remover
- Se não for usado, remover o app
- Relatórios podem ser parte de `monitoring`

---

## 3. Padrão de Migração

### 3.1 Processo para Cada App

**Passo 1: Criar estrutura nova (sem quebrar)**
```bash
# Criar novos arquivos vazios
touch apps/monitoring/forms.py
touch apps/monitoring/permissions.py
touch apps/monitoring/selectors.py
touch apps/monitoring/validators.py
touch apps/monitoring/serializers.py
mkdir apps/monitoring/views
touch apps/monitoring/views/__init__.py
```

**Passo 2: Mover código gradualmente**
```python
# Em views/__init__.py - manter compatibilidade
from .dashboard_views import DashboardView
from .agent_views import AgentListView, AgentDetailView
# ...

# Re-exportar para manter imports existentes funcionando
__all__ = ['DashboardView', 'AgentListView', ...]
```

**Passo 3: Extrair para services**
```python
# Antes (em views.py)
class DashboardView:
    def get_context_data(self):
        # 300 linhas de lógica

# Depois (em views/dashboard_views.py)
class DashboardView:
    def get_context_data(self):
        metrics = metrics_service.calculate_operator_metrics(...)
        alerts = alerts_service.build_operational_alerts(...)
        rankings = ranking_service.build_pause_rankings(...)
        # Apenas orquestração
```

**Passo 4: Adicionar testes**
```python
# tests/test_services/test_metrics_service.py
def test_calculate_operator_metrics():
    # Testar lógica extraída
    pass
```

**Passo 5: Deprecar código antigo (se aplicável)**
```python
# views.py (antigo)
import warnings
warnings.warn(
    "Import from monitoring.views is deprecated. "
    "Use monitoring.views.dashboard_views instead.",
    DeprecationWarning
)
```

---

## 4. Convenções de Nomenclatura

### 4.1 Arquivos

- **Singular:** `model.py`, `form.py` (se único)
- **Plural:** `models.py`, `forms.py` (se múltiplos)
- **Sufixo descritivo:** `_service.py`, `_views.py`

### 4.2 Classes

- **Views:** `<Nome>View`, `<Nome>ListView`, `<Nome>DetailView`
- **Forms:** `<Model>Form`, `<Ação>Form`
- **Services:** `<Domínio>Service` ou funções
- **Permissions:** `Can<Ação><Recurso>`

### 4.3 Funções

- **Selectors:** `get_<recurso>`, `list_<recursos>`, `filter_<recursos>`
- **Services:** `create_<recurso>`, `update_<recurso>`, `calculate_<métrica>`
- **Validators:** `validate_<campo>`
- **Serializers:** `serialize_<recurso>`

---

## 5. Checklist de Migração por App

### ✅ Monitoring (Prioritário)
- [ ] Criar `forms.py`
- [ ] Criar `permissions.py`
- [ ] Criar `selectors.py`
- [ ] Criar `validators.py`
- [ ] Criar `serializers.py`
- [ ] Criar `views/` e dividir `views.py`
- [ ] Criar `services/metrics_service.py`
- [ ] Criar `services/alerts_service.py`
- [ ] Criar `services/ranking_service.py`
- [ ] Criar `services/agent_service.py`
- [ ] Organizar `tests/`
- [ ] Adicionar testes para novos services

### ✅ Rules (Prioritário)
- [ ] Criar `urls.py`
- [ ] Criar `views.py`
- [ ] Criar `forms.py`
- [ ] Criar `permissions.py`
- [ ] Criar `selectors.py`
- [ ] Criar `validators.py`
- [ ] Criar templates
- [ ] Adicionar testes

### ✅ Messaging (Média Prioridade)
- [ ] Criar `urls.py`
- [ ] Criar `views.py`
- [ ] Criar `forms.py`
- [ ] Criar `permissions.py`
- [ ] Criar `selectors.py`
- [ ] Criar `services/`
- [ ] Criar templates
- [ ] Adicionar testes

### ✅ Integrations (Média Prioridade)
- [ ] Criar `urls.py`
- [ ] Criar `views.py`
- [ ] Criar `forms.py`
- [ ] Criar `permissions.py`
- [ ] Criar `selectors.py`
- [ ] Criar `services/`
- [ ] Criar templates
- [ ] Adicionar testes

### ✅ Assistant (Baixa Prioridade)
- [ ] Criar `forms.py`
- [ ] Criar `permissions.py`
- [ ] Criar `selectors.py`
- [ ] Adicionar mais testes

### ✅ Accounts (Baixa Prioridade)
- [ ] Criar `models.py` (User profile)
- [ ] Criar `views.py`
- [ ] Criar `forms.py`
- [ ] Criar `permissions.py`
- [ ] Expandir templates
- [ ] Adicionar testes

### ✅ Reports (Decidir)
- [ ] Implementar ou remover

---

## 6. Benefícios da Nova Estrutura

### 6.1 Manutenibilidade
- ✅ Arquivos menores e focados
- ✅ Fácil encontrar código
- ✅ Fácil adicionar features
- ✅ Fácil fazer code review

### 6.2 Testabilidade
- ✅ Testes organizados por tipo
- ✅ Fácil testar services isoladamente
- ✅ Fácil mockar dependências
- ✅ Cobertura de testes melhor

### 6.3 Reusabilidade
- ✅ Selectors reutilizáveis
- ✅ Services reutilizáveis
- ✅ Validators reutilizáveis
- ✅ Forms reutilizáveis

### 6.4 Escalabilidade
- ✅ Fácil adicionar novos apps
- ✅ Fácil adicionar novas features
- ✅ Fácil adicionar novos desenvolvedores
- ✅ Padrão consistente

---

## 7. Próximos Passos

1. Revisar e aprovar esta proposta
2. Consultar **PLANO_REFATORACAO.md** para ordem de execução
3. Consultar **ARQUIVOS_PRIORIDADE.md** para lista detalhada
4. Iniciar refatoração incremental

---

**Documento gerado automaticamente pela análise técnica do projeto.**  
**Nenhuma alteração foi feita no código durante esta análise.**
