# Arquivos a Alterar Primeiro - Lista Priorizada

**Data:** 18 de Março de 2026  
**Versão:** 1.0  
**Status:** Proposta sem implementação

---

## 1. Prioridade CRÍTICA (Semana 1-2)

### 1.1 Criar Estrutura Base

**Objetivo:** Criar arquivos vazios sem quebrar nada

#### Monitoring
```bash
# Criar arquivos
touch apps/monitoring/forms.py
touch apps/monitoring/permissions.py
touch apps/monitoring/selectors.py
touch apps/monitoring/validators.py
touch apps/monitoring/serializers.py
mkdir -p apps/monitoring/tests/test_services
touch apps/monitoring/tests/__init__.py
```

**Arquivos:**
- `apps/monitoring/forms.py` - NOVO
- `apps/monitoring/permissions.py` - NOVO
- `apps/monitoring/selectors.py` - NOVO
- `apps/monitoring/validators.py` - NOVO
- `apps/monitoring/serializers.py` - NOVO
- `apps/monitoring/tests/__init__.py` - NOVO

#### Rules
```bash
touch apps/rules/forms.py
touch apps/rules/permissions.py
touch apps/rules/selectors.py
touch apps/rules/validators.py
touch apps/rules/urls.py
touch apps/rules/views.py
```

**Arquivos:**
- `apps/rules/forms.py` - NOVO
- `apps/rules/permissions.py` - NOVO
- `apps/rules/selectors.py` - NOVO
- `apps/rules/validators.py` - NOVO
- `apps/rules/urls.py` - NOVO
- `apps/rules/views.py` - NOVO

#### Messaging
```bash
touch apps/messaging/forms.py
touch apps/messaging/permissions.py
touch apps/messaging/selectors.py
touch apps/messaging/urls.py
touch apps/messaging/views.py
mkdir -p apps/messaging/services
touch apps/messaging/services/__init__.py
```

**Arquivos:**
- `apps/messaging/forms.py` - NOVO
- `apps/messaging/permissions.py` - NOVO
- `apps/messaging/selectors.py` - NOVO
- `apps/messaging/urls.py` - NOVO
- `apps/messaging/views.py` - NOVO
- `apps/messaging/services/__init__.py` - NOVO

#### Integrations
```bash
touch apps/integrations/forms.py
touch apps/integrations/permissions.py
touch apps/integrations/selectors.py
touch apps/integrations/urls.py
touch apps/integrations/views.py
mkdir -p apps/integrations/services
touch apps/integrations/services/__init__.py
```

**Arquivos:**
- `apps/integrations/forms.py` - NOVO
- `apps/integrations/permissions.py` - NOVO
- `apps/integrations/selectors.py` - NOVO
- `apps/integrations/urls.py` - NOVO
- `apps/integrations/views.py` - NOVO
- `apps/integrations/services/__init__.py` - NOVO

#### Assistant
```bash
touch apps/assistant/forms.py
touch apps/assistant/permissions.py
touch apps/assistant/selectors.py
```

**Arquivos:**
- `apps/assistant/forms.py` - NOVO
- `apps/assistant/permissions.py` - NOVO
- `apps/assistant/selectors.py` - NOVO

#### Accounts
```bash
touch apps/accounts/forms.py
touch apps/accounts/permissions.py
touch apps/accounts/models.py
```

**Arquivos:**
- `apps/accounts/forms.py` - NOVO
- `apps/accounts/permissions.py` - NOVO
- `apps/accounts/models.py` - ALTERAR (adicionar User profile)

---

## 2. Prioridade ALTA (Semana 3-5)

### 2.1 Implementar Selectors (Monitoring)

**Objetivo:** Extrair queries ORM para camada reutilizável

**Arquivo:** `apps/monitoring/selectors.py`

**Funções a implementar:**
1. `get_active_agents()` - Agentes ativos
2. `get_events_for_period()` - Eventos por período
3. `get_day_stats_for_date()` - Estatísticas do dia
4. `get_workdays_for_date()` - Jornadas do dia
5. `get_pause_events_for_period()` - Eventos de pausa
6. `get_agent_by_code()` - Buscar agente por código
7. `get_recent_job_runs()` - Execuções recentes
8. `get_active_pause_classifications()` - Classificações ativas

**Impacto:** 
- Reduz duplicação de queries
- Facilita otimização
- Melhora testabilidade

**Arquivos a alterar:**
- ✅ `apps/monitoring/selectors.py` - IMPLEMENTAR
- ⚠️ `apps/monitoring/views.py` - REFATORAR (usar selectors)
- ✅ `apps/monitoring/tests/test_selectors.py` - CRIAR

### 2.2 Criar Testes para Selectors

**Arquivo:** `apps/monitoring/tests/test_selectors.py`

**Testes a criar:**
- `test_get_active_agents()`
- `test_get_events_for_period()`
- `test_get_events_filters_by_source()`
- `test_get_events_filters_by_agent_ids()`
- `test_get_day_stats_for_date()`
- `test_get_pause_events_excludes_names()`

**Impacto:**
- Garante comportamento correto
- Documenta uso esperado
- Facilita refatoração futura

---

## 3. Prioridade ALTA (Semana 6-8)

### 3.1 Extrair Services de Métricas

**Objetivo:** Mover cálculos complexos para services

**Arquivo:** `apps/monitoring/services/metrics_service.py` - CRIAR

**Funções a extrair de `views.py`:**
1. `calculate_operator_metrics()` - De `DashboardView._build_operator_metrics()`
2. `calculate_operational_score()` - De `DashboardView._calculate_operational_score()`
3. `calculate_health_score()` - De `DashboardView._calculate_health_score()`
4. `calculate_pause_distribution()` - De lógica inline
5. `calculate_occupancy_rate()` - De lógica inline

**Linhas a mover:** ~500 linhas de `views.py`

**Arquivos a alterar:**
- ✅ `apps/monitoring/services/metrics_service.py` - CRIAR
- ⚠️ `apps/monitoring/views.py` - REFATORAR (reduzir 500 linhas)
- ✅ `apps/monitoring/tests/test_services/test_metrics_service.py` - CRIAR

### 3.2 Extrair Services de Alertas

**Arquivo:** `apps/monitoring/services/alerts_service.py` - CRIAR

**Funções a extrair:**
1. `build_operational_alerts()` - De `DashboardView._build_operational_alerts()`
2. `detect_no_activity()` - De lógica inline
3. `detect_excessive_pauses()` - De lógica inline
4. `detect_low_occupancy()` - De lógica inline
5. `detect_event_gaps()` - De lógica inline

**Linhas a mover:** ~300 linhas de `views.py`

**Arquivos a alterar:**
- ✅ `apps/monitoring/services/alerts_service.py` - CRIAR
- ⚠️ `apps/monitoring/views.py` - REFATORAR (reduzir 300 linhas)
- ✅ `apps/monitoring/tests/test_services/test_alerts_service.py` - CRIAR

### 3.3 Extrair Services de Rankings

**Arquivo:** `apps/monitoring/services/ranking_service.py` - CRIAR

**Funções a extrair:**
1. `build_pause_rankings()` - De `DashboardView._build_pause_rankings()`
2. `build_productivity_ranking()` - De `DashboardView._build_productivity_ranking()`
3. `build_gamified_leaderboard()` - De `DashboardView._build_gamified_leaderboard()`
4. `attach_bar_percentages()` - De `DashboardView._attach_bar_pct()`

**Linhas a mover:** ~200 linhas de `views.py`

**Arquivos a alterar:**
- ✅ `apps/monitoring/services/ranking_service.py` - CRIAR
- ⚠️ `apps/monitoring/views.py` - REFATORAR (reduzir 200 linhas)
- ✅ `apps/monitoring/tests/test_services/test_ranking_service.py` - CRIAR

---

## 4. Prioridade MÉDIA (Semana 9-12)

### 4.1 Dividir Views Gigante

**Objetivo:** Quebrar `views.py` em múltiplos arquivos

**Estrutura alvo:**
```
apps/monitoring/views/
├── __init__.py          - Re-exportar tudo
├── dashboard_views.py   - Dashboards (4 classes)
├── agent_views.py       - Agentes (4 classes)
├── job_views.py         - Jobs (2 classes)
├── pause_views.py       - Pausas (1 classe)
└── config_views.py      - Configurações (NOVO)
```

**Arquivos a criar:**
- ✅ `apps/monitoring/views/__init__.py` - CRIAR
- ✅ `apps/monitoring/views/dashboard_views.py` - CRIAR (mover 4 classes)
- ✅ `apps/monitoring/views/agent_views.py` - CRIAR (mover 2 classes + 2 novas)
- ✅ `apps/monitoring/views/job_views.py` - CRIAR (mover 2 classes)
- ✅ `apps/monitoring/views/pause_views.py` - CRIAR (mover 1 classe)
- ✅ `apps/monitoring/views/config_views.py` - CRIAR (novas views)

**Arquivos a deprecar:**
- ⚠️ `apps/monitoring/views.py` - DEPRECAR (manter por compatibilidade)

**Classes a mover:**

**Para `dashboard_views.py`:**
- `DashboardView` (635 linhas → ~150 linhas após refatoração)
- `DashboardProductivityView`
- `DashboardRiskView`
- `DashboardPipelineView`
- `DashboardDayDetailView`
- `DashboardRebuildStatsView`

**Para `agent_views.py`:**
- `AgentListView` (existente)
- `AgentDetailView` (existente)
- `AgentCreateView` (NOVO)
- `AgentUpdateView` (NOVO)

**Para `job_views.py`:**
- `JobRunListView`
- `JobRunDetailView`

**Para `pause_views.py`:**
- `PauseClassificationConfigView`

### 4.2 Implementar Forms

**Arquivo:** `apps/monitoring/forms.py`

**Forms a criar:**
1. `DashboardFilterForm` - Filtros de dashboard
2. `AgentForm` - Cadastro/edição de agente
3. `PauseClassificationForm` - Classificação de pausas
4. `JobRunFilterForm` - Filtros de execuções

**Arquivos a alterar:**
- ✅ `apps/monitoring/forms.py` - IMPLEMENTAR
- ⚠️ `apps/monitoring/views/dashboard_views.py` - USAR forms
- ⚠️ `apps/monitoring/views/agent_views.py` - USAR forms
- ✅ `apps/monitoring/tests/test_forms.py` - CRIAR

### 4.3 Implementar Permissions

**Arquivo:** `apps/monitoring/permissions.py`

**Permissions a criar:**
1. `CanViewDashboard` - Ver dashboards
2. `CanManageAgents` - Gerenciar agentes
3. `CanRebuildStats` - Rebuild estatísticas
4. `CanManagePauseClassification` - Gerenciar classificações

**Arquivos a alterar:**
- ✅ `apps/monitoring/permissions.py` - IMPLEMENTAR
- ⚠️ `apps/monitoring/views/dashboard_views.py` - USAR permissions
- ⚠️ `apps/monitoring/views/agent_views.py` - USAR permissions
- ✅ `apps/monitoring/tests/test_permissions.py` - CRIAR

### 4.4 Implementar Validators

**Arquivo:** `apps/monitoring/validators.py`

**Validators a criar:**
1. `validate_operator_code()` - Código de operador
2. `validate_date_range()` - Range de datas
3. `validate_pause_name()` - Nome de pausa
4. `validate_email_or_ramal()` - Email ou ramal

**Arquivos a alterar:**
- ✅ `apps/monitoring/validators.py` - IMPLEMENTAR
- ⚠️ `apps/monitoring/forms.py` - USAR validators
- ⚠️ `apps/monitoring/models.py` - USAR validators (opcional)

---

## 5. Prioridade MÉDIA (Semana 13-15)

### 5.1 Criar Tela de Configurações (Rules)

**Objetivo:** Substituir admin para configurações

**Arquivos a criar:**
- ✅ `apps/rules/urls.py` - CRIAR
- ✅ `apps/rules/views.py` - IMPLEMENTAR
- ✅ `apps/rules/forms.py` - IMPLEMENTAR
- ✅ `apps/rules/permissions.py` - IMPLEMENTAR
- ✅ `templates/rules/config_list.html` - CRIAR
- ✅ `templates/rules/config_edit.html` - CRIAR

**Arquivos a alterar:**
- ⚠️ `alive_platform/urls.py` - ADICIONAR include('apps.rules.urls')
- ⚠️ `templates/layouts/base.html` - ADICIONAR link no menu

**Views a criar:**
1. `ConfigListView` - Lista de configurações
2. `ConfigEditView` - Edição de configuração

**Forms a criar:**
1. `SystemConfigForm` - Formulário de configuração

**Permissions a criar:**
1. `CanManageConfigs` - Gerenciar configurações

### 5.2 Criar Tela de Templates de Mensagens (Messaging)

**Objetivo:** Substituir admin para templates

**Arquivos a criar:**
- ✅ `apps/messaging/urls.py` - CRIAR
- ✅ `apps/messaging/views.py` - IMPLEMENTAR
- ✅ `apps/messaging/forms.py` - IMPLEMENTAR
- ✅ `apps/messaging/permissions.py` - IMPLEMENTAR
- ✅ `apps/messaging/services/template_service.py` - CRIAR
- ✅ `templates/messaging/template_list.html` - CRIAR
- ✅ `templates/messaging/template_edit.html` - CRIAR
- ✅ `templates/messaging/template_preview.html` - CRIAR

**Arquivos a alterar:**
- ⚠️ `alive_platform/urls.py` - ADICIONAR include('apps.messaging.urls')
- ⚠️ `templates/layouts/base.html` - ADICIONAR link no menu

**Views a criar:**
1. `TemplateListView` - Lista de templates
2. `TemplateCreateView` - Criar template
3. `TemplateUpdateView` - Editar template
4. `TemplatePreviewView` - Preview de template

**Services a criar:**
1. `render_template()` - Renderizar template
2. `get_active_template()` - Buscar template ativo

### 5.3 Expandir Tela de Gestão de Agentes

**Objetivo:** CRUD completo de agentes

**Arquivos a criar:**
- ✅ `templates/monitoring/agent_form.html` - CRIAR

**Arquivos a alterar:**
- ⚠️ `apps/monitoring/urls.py` - ADICIONAR rotas CRUD
- ⚠️ `apps/monitoring/views/agent_views.py` - ADICIONAR views CRUD
- ⚠️ `templates/monitoring/agents_list.html` - ADICIONAR botões

**Views a adicionar:**
1. `AgentCreateView` - Criar agente
2. `AgentUpdateView` - Editar agente
3. `AgentDeactivateView` - Desativar agente

---

## 6. Prioridade BAIXA (Semana 16+)

### 6.1 Organizar Testes

**Objetivo:** Dividir arquivo gigante de testes

**Estrutura alvo:**
```
apps/monitoring/tests/
├── __init__.py
├── test_models.py
├── test_views.py
├── test_forms.py
├── test_selectors.py
├── test_permissions.py
├── test_validators.py
├── test_services/
│   ├── test_metrics_service.py
│   ├── test_alerts_service.py
│   ├── test_ranking_service.py
│   ├── test_day_stats_service.py
│   ├── test_pause_classification.py
│   └── test_risk_scoring.py
└── fixtures/
    └── test_data.json
```

**Arquivos a criar:**
- ✅ Todos os arquivos acima

**Arquivos a deprecar:**
- ⚠️ `apps/monitoring/tests.py` - DEPRECAR (50889 linhas!)
- ⚠️ `apps/monitoring/tests_*.py` - MOVER para pasta tests/

### 6.2 Melhorar App Assistant

**Objetivo:** Adicionar camadas faltantes

**Arquivos a criar:**
- ✅ `apps/assistant/forms.py` - IMPLEMENTAR
- ✅ `apps/assistant/permissions.py` - IMPLEMENTAR
- ✅ `apps/assistant/selectors.py` - IMPLEMENTAR

**Forms a criar:**
1. `UserPreferenceForm` - Preferências do usuário

**Permissions a criar:**
1. `CanUseAssistant` - Usar assistente
2. `CanManageConversations` - Gerenciar conversas

**Selectors a criar:**
1. `get_user_conversations()` - Conversas do usuário
2. `get_conversation_with_messages()` - Conversa com mensagens

### 6.3 Melhorar App Accounts

**Objetivo:** Adicionar funcionalidades de perfil

**Arquivos a criar:**
- ✅ `apps/accounts/models.py` - IMPLEMENTAR (User profile)
- ✅ `apps/accounts/forms.py` - IMPLEMENTAR
- ✅ `apps/accounts/views.py` - IMPLEMENTAR
- ✅ `templates/accounts/profile.html` - CRIAR
- ✅ `templates/accounts/change_password.html` - CRIAR

**Arquivos a alterar:**
- ⚠️ `apps/accounts/urls.py` - ADICIONAR rotas
- ⚠️ `templates/layouts/base.html` - ADICIONAR link perfil

### 6.4 Decidir sobre App Reports

**Opção 1: Implementar**
- Criar estrutura completa
- Adicionar geração de relatórios
- Adicionar exportação PDF/Excel

**Opção 2: Remover**
- Remover app
- Relatórios ficam em `monitoring`

**Recomendação:** Remover por enquanto, implementar depois se necessário

---

## 7. Resumo de Impacto por Arquivo

### Arquivos Críticos (Alto Impacto)

| Arquivo | Linhas Atuais | Linhas Alvo | Redução | Prioridade |
|---------|---------------|-------------|---------|------------|
| `apps/monitoring/views.py` | 2368 | 500 | -79% | CRÍTICA |
| `apps/monitoring/tests.py` | 50889 | 0 | -100% | ALTA |
| `apps/monitoring/selectors.py` | 0 | 300 | +300 | ALTA |
| `apps/monitoring/services/metrics_service.py` | 0 | 500 | +500 | ALTA |
| `apps/monitoring/services/alerts_service.py` | 0 | 300 | +300 | ALTA |
| `apps/monitoring/services/ranking_service.py` | 0 | 200 | +200 | ALTA |

### Arquivos Novos (Funcionalidades)

| Arquivo | Propósito | Linhas Estimadas | Prioridade |
|---------|-----------|------------------|------------|
| `apps/rules/views.py` | Tela de configs | 150 | MÉDIA |
| `apps/messaging/views.py` | Tela de templates | 200 | MÉDIA |
| `apps/monitoring/views/agent_views.py` | CRUD agentes | 150 | MÉDIA |
| `apps/monitoring/forms.py` | Validações | 200 | MÉDIA |
| `apps/monitoring/permissions.py` | Controle acesso | 100 | MÉDIA |

### Arquivos de Suporte

| Arquivo | Propósito | Linhas Estimadas | Prioridade |
|---------|-----------|------------------|------------|
| `apps/monitoring/validators.py` | Validações domínio | 100 | MÉDIA |
| `apps/monitoring/serializers.py` | Formatação saída | 150 | BAIXA |
| `apps/assistant/forms.py` | Forms assistant | 50 | BAIXA |
| `apps/assistant/permissions.py` | Permissions assistant | 50 | BAIXA |
| `apps/assistant/selectors.py` | Queries assistant | 100 | BAIXA |

---

## 8. Ordem de Execução Recomendada

### Fase 1: Fundação (Semana 1-2)
1. ✅ Criar todos os arquivos vazios
2. ✅ Adicionar docstrings base
3. ✅ Configurar estrutura de testes
4. ✅ Commit: "feat: add base architecture structure"

### Fase 2: Queries (Semana 3-5)
5. ✅ Implementar `selectors.py` em monitoring
6. ✅ Criar testes para selectors
7. ✅ Refatorar views para usar selectors
8. ✅ Commit: "refactor: extract queries to selectors"

### Fase 3: Lógica de Negócio (Semana 6-8)
9. ✅ Criar `services/metrics_service.py`
10. ✅ Criar `services/alerts_service.py`
11. ✅ Criar `services/ranking_service.py`
12. ✅ Criar testes para services
13. ✅ Refatorar views para usar services
14. ✅ Commit: "refactor: extract business logic to services"

### Fase 4: Validação e Controle (Semana 9-12)
15. ✅ Dividir `views.py` em múltiplos arquivos
16. ✅ Implementar `forms.py`
17. ✅ Implementar `permissions.py`
18. ✅ Implementar `validators.py`
19. ✅ Criar testes
20. ✅ Aplicar em views
21. ✅ Commit: "feat: add forms, validators and permissions"

### Fase 5: Interfaces Web (Semana 13-15)
22. ✅ Criar tela de configurações (rules)
23. ✅ Criar tela de templates (messaging)
24. ✅ Expandir gestão de agentes (monitoring)
25. ✅ Atualizar navegação
26. ✅ Commit: "feat: add web interfaces to replace admin"

### Fase 6: Refinamento (Semana 16+)
27. ✅ Organizar testes
28. ✅ Melhorar assistant
29. ✅ Melhorar accounts
30. ✅ Decidir sobre reports
31. ✅ Commit: "refactor: organize tests and improve apps"

---

## 9. Checklist de Validação

### Após Cada Fase

- [ ] Todos os testes passam
- [ ] `python manage.py check` sem erros
- [ ] Dashboards funcionam corretamente
- [ ] Performance mantida ou melhorada
- [ ] Sem regressões visuais
- [ ] Code review aprovado
- [ ] Documentação atualizada
- [ ] Deploy em staging OK
- [ ] Monitoramento sem alertas

### Antes de Cada Commit

- [ ] Código formatado (black, isort)
- [ ] Linting OK (flake8, pylint)
- [ ] Type hints adicionados (mypy)
- [ ] Docstrings completas
- [ ] Testes adicionados/atualizados
- [ ] Changelog atualizado

---

## 10. Ferramentas de Apoio

### Análise de Código
```bash
# Complexidade ciclomática
radon cc apps/monitoring/views.py -a

# Duplicação de código
pylint --disable=all --enable=duplicate-code apps/

# Cobertura de testes
coverage run --source='apps' manage.py test
coverage report
coverage html
```

### Refatoração
```bash
# Renomear símbolos
rope refactor apps/monitoring/views.py

# Extrair função
# Usar IDE (PyCharm, VSCode)
```

### Performance
```bash
# Profiling
python -m cProfile -o profile.stats manage.py runserver

# Análise de queries
python manage.py debugsqlshell

# Django Debug Toolbar
# Adicionar ao INSTALLED_APPS
```

---

## 11. Documentação a Atualizar

### Durante Refatoração
- [ ] `docs/ARCHITECTURE.md` - Atualizar arquitetura
- [ ] `docs/estrutura_do_projeto.md` - Atualizar estrutura
- [ ] `README.md` - Atualizar instruções
- [ ] Docstrings inline - Adicionar em todos os módulos

### Após Refatoração
- [ ] Guia de desenvolvimento - Criar
- [ ] Guia de testes - Criar
- [ ] Guia de deployment - Atualizar
- [ ] Changelog - Documentar mudanças

---

## 12. Comunicação com Equipe

### Antes de Iniciar
- [ ] Apresentar diagnóstico técnico
- [ ] Apresentar plano de refatoração
- [ ] Obter aprovação
- [ ] Definir responsáveis

### Durante Execução
- [ ] Daily updates
- [ ] Code reviews
- [ ] Pair programming (partes críticas)
- [ ] Demos semanais

### Após Conclusão
- [ ] Retrospectiva
- [ ] Documentação de lições aprendidas
- [ ] Treinamento da equipe
- [ ] Celebração! 🎉

---

**Documento gerado automaticamente pela análise técnica do projeto.**  
**Nenhuma alteração foi feita no código durante esta análise.**
