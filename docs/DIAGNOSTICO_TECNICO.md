# Diagnóstico Técnico Completo - NEF Cadência v2

**Data:** 18 de Março de 2026  
**Versão:** 1.0  
**Status:** Análise sem implementação

---

## 1. Arquitetura Atual do Backend

### 1.1 Stack Tecnológica
- **Framework:** Django 5.1
- **Banco de Dados:** PostgreSQL
- **Renderização:** Server-side templates (Django Templates)
- **Frontend:** TailwindCSS + JavaScript vanilla
- **IA:** OpenAI GPT-4.1-mini

### 1.2 Estrutura de Apps Django

```
alive_platform/          # Projeto principal (settings, urls)
apps/
├── accounts/           # Autenticação e usuários
├── monitoring/         # Monitoramento operacional (CORE)
├── rules/              # Configurações do sistema
├── messaging/          # Templates de mensagens
├── integrations/       # Integrações externas
├── reports/            # Relatórios (vazio)
└── assistant/          # Assistente IA com OpenAI
```

### 1.3 Padrão de Organização Atual
- **Models:** Definição de dados e lógica de domínio
- **Views:** Lógica de apresentação e orquestração
- **Admin:** Interface administrativa Django
- **Services:** Camada de lógica de negócio (parcial)
- **Templates:** Renderização server-side
- **Management Commands:** Jobs e tarefas assíncronas

---

## 2. Responsabilidades de Cada App

### 2.1 `accounts` - Autenticação
**Responsabilidade:** Gerenciamento de login/logout  
**Estado:** Minimalista, usa views padrão do Django  
**Arquivos principais:**
- `urls.py` - Rotas de login/logout
- `context_processors.py` - Contexto para menu admin
- `templatetags/admin_menu.py` - Tags customizadas

**Problemas:**
- Não possui views customizadas
- Não possui forms próprios
- Não possui models de usuário estendido
- Depende 100% do admin do Django

### 2.2 `monitoring` - Monitoramento Operacional (CORE)
**Responsabilidade:** Monitoramento de agentes, eventos, pausas, dashboards  
**Estado:** App principal com 102KB de views (2368 linhas!)  
**Arquivos principais:**
- `models.py` (481 linhas) - 10 models
- `views.py` (2368 linhas) - **CRÍTICO: arquivo gigante**
- `admin.py` (100 linhas)
- `services/` - 6 arquivos de serviços
- `management/commands/` - 10 commands

**Models:**
- `Agent` - Operadores
- `AgentEvent` - Eventos de agentes (protegido)
- `AgentWorkday` - Jornadas diárias (protegido)
- `AgentDayStats` - Estatísticas agregadas
- `PauseClassification` - Classificação de pausas
- `NotificationHistory` - Histórico de notificações
- `NotificationThrottle` - Controle de envio
- `JobRun` - Execuções de jobs

**Views (Classes):**
1. `DashboardView` - Dashboard executivo (635 linhas de lógica!)
2. `DashboardProductivityView` - Dashboard produtividade
3. `DashboardRiskView` - Dashboard risco
4. `DashboardPipelineView` - Dashboard pipeline
5. `DashboardDayDetailView` - Detalhes do dia
6. `DashboardRebuildStatsView` - Rebuild de estatísticas
7. `PauseClassificationConfigView` - Configuração de pausas
8. `AgentListView` - Lista de agentes
9. `AgentDetailView` - Detalhe do agente
10. `JobRunListView` - Lista de execuções
11. `JobRunDetailView` - Detalhe de execução

**Problemas Críticos:**
- `views.py` com 2368 linhas é **inaceitável**
- `DashboardView` tem lógica de negócio misturada com apresentação
- Cálculos complexos dentro das views (scoring, rankings, alertas)
- Queries ORM espalhadas pelas views
- Falta camada de selectors para queries
- Falta camada de forms para validação
- Falta camada de permissions
- Dependências circulares com `messaging`

### 2.3 `assistant` - Assistente IA
**Responsabilidade:** Chat com IA, ferramentas, guardrails  
**Estado:** Bem estruturado com services  
**Arquivos principais:**
- `models.py` (232 linhas) - 5 models
- `views.py` (473 linhas) - Views funcionais
- `services/` - 20 arquivos (bem organizado!)
- `tests/` - 14 arquivos de testes

**Models:**
- `AssistantConversation` - Conversas
- `AssistantMessage` - Mensagens
- `AssistantActionLog` - Log de ações
- `AssistantAuditLog` - Auditoria
- `AssistantUserPreference` - Preferências

**Services (Exemplar):**
- `assistant_service.py` - Orquestração principal
- `capabilities.py` - Capacidades do assistente
- `guardrails.py` - Regras de segurança
- `semantic_resolution.py` - Resolução semântica
- `tools_actions.py` - Ferramentas de ação
- `tools_read.py` - Ferramentas de leitura
- `conversation_store.py` - Persistência
- `widget_session_service.py` - Sessões widget

**Pontos Positivos:**
- ✅ Camada de services bem definida
- ✅ Separação de responsabilidades
- ✅ Testes unitários
- ✅ Observabilidade (logs de auditoria)

**Problemas:**
- Views ainda tem alguma lógica que poderia estar em services
- Falta camada de permissions explícita
- Falta forms para validação de entrada

### 2.4 `rules` - Configurações do Sistema
**Responsabilidade:** Configurações dinâmicas  
**Estado:** Simples, funcional  
**Arquivos:**
- `models.py` - `SystemConfig` model
- `services/system_config.py` - Service para leitura
- `admin.py` - Interface admin

**Problemas:**
- Totalmente dependente do admin
- Deveria ter uma tela própria de configurações
- Falta validação de tipos
- Falta versionamento de configs

### 2.5 `messaging` - Templates de Mensagens
**Responsabilidade:** Templates de notificações  
**Estado:** Simples, apenas models  
**Arquivos:**
- `models.py` - `MessageTemplate` model
- `choices.py` - Enums de canais e tipos
- `admin.py` - Interface admin

**Problemas:**
- Não possui service de envio
- Não possui views próprias
- Totalmente no admin
- Falta integração real com canais

### 2.6 `integrations` - Integrações Externas
**Responsabilidade:** Configuração de integrações  
**Estado:** Apenas estrutura, sem implementação  
**Arquivos:**
- `models.py` - `Integration` model
- `admin.py` - Interface admin

**Problemas:**
- Não possui implementação real
- Não possui services
- Apenas configuração no admin

### 2.7 `reports` - Relatórios
**Responsabilidade:** Geração de relatórios  
**Estado:** **VAZIO** - apenas estrutura Django  
**Problemas:**
- App criado mas não implementado
- Deveria ser removido ou implementado

---

## 3. Problemas de Organização de Pastas

### 3.1 Estrutura Atual
```
apps/
├── monitoring/
│   ├── models.py (481 linhas)
│   ├── views.py (2368 linhas) ❌ CRÍTICO
│   ├── admin.py
│   ├── services/ ✅
│   ├── management/commands/ ✅
│   └── tests.py (50889 linhas) ❌
```

### 3.2 Problemas Identificados

#### ❌ Falta de Camadas Essenciais
- **Sem `forms.py`** em nenhum app
- **Sem `permissions.py`** em nenhum app
- **Sem `validators.py`** em nenhum app
- **Sem `selectors.py`** em nenhum app
- **Sem `serializers.py`** (se precisar API REST)

#### ❌ Arquivos Gigantes
- `monitoring/views.py` - 2368 linhas
- `monitoring/tests.py` - 50889 linhas
- `assistant/services/assistant_service.py` - 58408 bytes

#### ❌ Testes Mal Organizados
- Testes em arquivo único gigante (`monitoring/tests.py`)
- Alguns testes em arquivos separados (`tests_*.py`)
- Falta pasta `tests/` estruturada

#### ✅ Pontos Positivos
- `services/` bem usado em `monitoring` e `assistant`
- `management/commands/` bem estruturado
- Separação de apps por domínio

---

## 4. Views Muito Grandes

### 4.1 `monitoring/views.py` - 2368 linhas

**Classe `DashboardView`:**
- 635+ linhas de lógica
- Responsabilidades misturadas:
  - Queries ORM complexas
  - Cálculos de métricas
  - Agregações
  - Scoring de risco
  - Rankings
  - Alertas
  - Formatação de dados
  - Lógica de apresentação

**Métodos problemáticos:**
```python
def get_context_data(self, **kwargs):  # 300+ linhas
    # Queries
    # Agregações
    # Cálculos
    # Formatação
    # Tudo misturado!
```

**Outros métodos:**
- `_build_operator_metrics()` - Lógica de negócio
- `_build_pause_rankings()` - Agregação
- `_build_risk_agents()` - Scoring
- `_build_operational_alerts()` - Regras de negócio
- `_calculate_operational_score()` - Cálculo
- `_build_gamified_leaderboard()` - Apresentação

### 4.2 Responsabilidades Misturadas

**O que está nas views mas NÃO deveria:**
1. **Queries complexas** → deveria estar em `selectors.py`
2. **Cálculos de métricas** → deveria estar em `services/metrics_service.py`
3. **Scoring de risco** → já existe `services/risk_scoring.py` mas não é usado
4. **Regras de alertas** → deveria estar em `services/alerts_service.py`
5. **Agregações** → deveria estar em `selectors.py`
6. **Validações** → deveria estar em `validators.py`
7. **Formatação de dados** → deveria estar em `serializers.py` ou helpers

---

## 5. Ausência de Camadas Essenciais

### 5.1 Forms (Validação de Entrada)
**Status:** ❌ Não existe em nenhum app

**Impacto:**
- Validação feita nas views
- Código duplicado
- Difícil testar
- Sem reuso

**Onde deveria existir:**
- `monitoring/forms.py` - Filtros de dashboard, classificação de pausas
- `rules/forms.py` - Configurações do sistema
- `messaging/forms.py` - Templates de mensagens
- `assistant/forms.py` - Preferências do usuário

### 5.2 Permissions (Controle de Acesso)
**Status:** ❌ Não existe em nenhum app

**Impacto:**
- Permissões hardcoded nas views (`is_staff`)
- Sem granularidade
- Difícil auditar
- Sem reuso

**Onde deveria existir:**
- `monitoring/permissions.py` - Permissões de dashboard, rebuild stats
- `rules/permissions.py` - Quem pode alterar configs
- `assistant/permissions.py` - Limites de conversas

### 5.3 Selectors (Queries Reutilizáveis)
**Status:** ❌ Não existe em nenhum app

**Impacto:**
- Queries ORM espalhadas pelas views
- Código duplicado
- Difícil otimizar
- Difícil testar

**Onde deveria existir:**
- `monitoring/selectors.py` - Queries de agentes, eventos, estatísticas
- `assistant/selectors.py` - Queries de conversas, mensagens

### 5.4 Validators (Validações de Domínio)
**Status:** ❌ Não existe em nenhum app

**Impacto:**
- Validações nos models ou views
- Sem reuso
- Difícil testar

**Onde deveria existir:**
- `monitoring/validators.py` - Validação de datas, operadores
- `rules/validators.py` - Validação de tipos de config

### 5.5 Serializers (Formatação de Saída)
**Status:** ❌ Não existe

**Impacto:**
- Formatação nas views
- Código duplicado
- Difícil manter consistência

**Onde deveria existir:**
- `monitoring/serializers.py` - Formatação de métricas, rankings
- `assistant/serializers.py` - Já tem funções `_serialize_*` mas não está organizado

---

## 6. Dependências Entre Apps

### 6.1 Mapa de Dependências

```
monitoring → messaging (TemplateTypeChoices, ChannelChoices)
monitoring → rules (indiretamente via services)
assistant → monitoring (via tools)
assistant → rules (via tools)
integrations → messaging (ChannelChoices)
```

### 6.2 Análise de Acoplamento

**Acoplamento Aceitável:**
- ✅ `monitoring` → `messaging` (notificações)
- ✅ `integrations` → `messaging` (canais)

**Acoplamento Problemático:**
- ⚠️ `assistant` → `monitoring` (via tools, mas aceitável)
- ⚠️ `assistant` → `rules` (via tools, mas aceitável)

**Imports Cruzados:**
- 127 imports de `from apps.` encontrados
- Maioria em `assistant` (esperado, é orquestrador)
- Alguns em `monitoring` (services)

### 6.3 Recomendações
- Manter dependências unidirecionais
- `assistant` pode depender de outros (é camada de aplicação)
- `monitoring`, `rules`, `messaging` devem ser independentes
- Considerar eventos/signals para desacoplar

---

## 7. Rotas Existentes

### 7.1 Rotas Principais (`alive_platform/urls.py`)
```python
/                          → Redirect para /dashboard
/login                     → Login
/logout                    → Logout
/dashboard*                → Monitoring app
/assistant/*               → Assistant app
/admin/                    → Django Admin
```

### 7.2 Rotas de Monitoring (`monitoring/urls.py`)
```python
/dashboard                                    → DashboardView
/dashboard/produtividade                      → DashboardProductivityView
/dashboard/risco                              → DashboardRiskView
/dashboard/pipeline                           → DashboardPipelineView
/dashboard/day-detail                         → DashboardDayDetailView
/dashboard/actions/rebuild-stats              → DashboardRebuildStatsView
/admin/monitoring/pause-classification        → PauseClassificationConfigView
/agents                                       → AgentListView
/agents/<int:pk>                              → AgentDetailView
/runs                                         → JobRunListView
/runs/<int:pk>                                → JobRunDetailView
```

### 7.3 Rotas de Assistant (`assistant/urls.py`)
```python
/assistant/                                   → assistant_page_view
/assistant/chat                               → assistant_chat_view
/assistant/conversations                      → assistant_page_conversations_view
/assistant/conversations/<int:id>             → assistant_page_conversation_detail_view
/assistant/conversations/<int:id>/delete      → assistant_page_delete_conversation_view
/assistant/conversation/<int:id>              → assistant_conversation_view
/assistant/widget/chat                        → assistant_widget_chat_view
/assistant/widget/session/end                 → assistant_widget_end_session_view
/assistant/widget/session/save                → assistant_widget_save_session_view
```

### 7.4 Análise de Rotas
- ✅ Rotas bem organizadas por domínio
- ✅ Uso de namespaces nos nomes
- ⚠️ Rota `/admin/monitoring/pause-classification` deveria ser `/monitoring/pause-classification`
- ❌ Faltam rotas para configurações do sistema
- ❌ Faltam rotas para templates de mensagens
- ❌ Faltam rotas para integrações

---

## 8. Telas Existentes e Telas Faltantes

### 8.1 Telas Implementadas

#### Monitoring (12 templates)
1. ✅ `dashboard_executive.html` - Dashboard executivo
2. ✅ `dashboard_productivity.html` - Dashboard produtividade
3. ✅ `dashboard_risk.html` - Dashboard risco
4. ✅ `dashboard_pipeline.html` - Dashboard pipeline
5. ✅ `dashboard_day_detail.html` - Detalhes do dia
6. ✅ `pause_classification.html` - Classificação de pausas
7. ✅ `agents_list.html` - Lista de agentes
8. ✅ `agent_detail.html` - Detalhe do agente
9. ✅ `runs_list.html` - Lista de execuções
10. ✅ `run_detail.html` - Detalhe de execução
11. ✅ `_dashboard_filters.html` - Filtros (partial)
12. ✅ `_dashboard_nav.html` - Navegação (partial)

#### Assistant (2 templates)
1. ✅ `page.html` - Página do assistente
2. ✅ Outros templates (widget, etc.)

#### Accounts (1 template)
1. ✅ `login.html` - Login

### 8.2 Telas Faltantes (Críticas)

#### ❌ Configurações do Sistema
**Atual:** Apenas no Django Admin  
**Deveria ter:**
- `/configuracoes` - Página de configurações
- Lista de configurações agrupadas
- Formulário de edição inline
- Histórico de alterações
- Validação visual de tipos

#### ❌ Templates de Mensagens
**Atual:** Apenas no Django Admin  
**Deveria ter:**
- `/mensagens` - Lista de templates
- `/mensagens/<id>` - Edição de template
- Preview de mensagem
- Teste de envio
- Histórico de versões

#### ❌ Integrações
**Atual:** Apenas no Django Admin  
**Deveria ter:**
- `/integracoes` - Lista de integrações
- `/integracoes/<id>` - Configuração
- Teste de conexão
- Logs de integração
- Status de saúde

#### ❌ Gestão de Agentes
**Atual:** Apenas no Django Admin  
**Deveria ter:**
- `/agentes/novo` - Cadastro de agente
- `/agentes/<id>/editar` - Edição de agente
- Ativação/desativação inline

#### ❌ Notificações
**Atual:** Apenas histórico no admin  
**Deveria ter:**
- `/notificacoes` - Dashboard de notificações
- Filtros por status, tipo, canal
- Reenvio de notificações
- Estatísticas

#### ❌ Relatórios
**Atual:** Não existe  
**Deveria ter:**
- `/relatorios` - Lista de relatórios
- Relatórios customizáveis
- Exportação (PDF, Excel)
- Agendamento

---

## 9. Dependência do Django Admin

### 9.1 O Que Está Apenas no Admin

#### Totalmente no Admin:
1. **SystemConfig** (`rules`) - Configurações do sistema
2. **MessageTemplate** (`messaging`) - Templates de mensagens
3. **Integration** (`integrations`) - Integrações
4. **Agent** (`monitoring`) - Cadastro de agentes
5. **AgentEvent** (`monitoring`) - Eventos (read-only)
6. **AgentWorkday** (`monitoring`) - Jornadas (read-only)
7. **AgentDayStats** (`monitoring`) - Estatísticas
8. **NotificationHistory** (`monitoring`) - Histórico
9. **NotificationThrottle** (`monitoring`) - Controle
10. **JobRun** (`monitoring`) - Execuções de jobs
11. **AssistantConversation** (`assistant`) - Conversas
12. **AssistantMessage** (`assistant`) - Mensagens
13. **AssistantActionLog** (`assistant`) - Logs de ação
14. **AssistantAuditLog** (`assistant`) - Auditoria
15. **AssistantUserPreference** (`assistant`) - Preferências

#### Parcialmente no Admin:
1. **PauseClassification** - Tem tela própria + admin

### 9.2 Impacto da Dependência do Admin

**Problemas:**
- ❌ UX ruim para usuários não técnicos
- ❌ Falta de contexto de negócio
- ❌ Sem workflows customizados
- ❌ Sem validações específicas
- ❌ Sem integrações visuais
- ❌ Difícil adicionar features customizadas

**Benefícios:**
- ✅ Rápido para prototipar
- ✅ CRUD automático
- ✅ Filtros e busca prontos

### 9.3 Priorização de Migração

**Alta Prioridade:**
1. **Configurações do Sistema** - Usado frequentemente
2. **Templates de Mensagens** - Crítico para operação
3. **Gestão de Agentes** - Cadastro frequente

**Média Prioridade:**
4. **Integrações** - Configuração esporádica
5. **Notificações** - Monitoramento importante

**Baixa Prioridade:**
6. **Logs do Assistant** - Apenas consulta
7. **Eventos/Workdays** - Read-only, pode ficar no admin

---

## 10. Proposta de Evolução do Backend

### 10.1 Princípios da Evolução

1. **Sem quebra de compatibilidade** - Evolução incremental
2. **Sem reescrita do zero** - Refatoração gradual
3. **Manter padrão atual** - Django server-side
4. **Adicionar camadas faltantes** - Forms, permissions, selectors
5. **Extrair lógica das views** - Para services
6. **Criar telas para substituir admin** - Gradualmente

### 10.2 Arquitetura Alvo

```
app/
├── models.py              # Apenas definição de dados
├── admin.py               # Admin simplificado (manter para casos específicos)
├── urls.py                # Rotas
├── views.py               # Apenas orquestração (< 300 linhas)
├── forms.py               # ✨ NOVO - Validação de entrada
├── permissions.py         # ✨ NOVO - Controle de acesso
├── selectors.py           # ✨ NOVO - Queries reutilizáveis
├── validators.py          # ✨ NOVO - Validações de domínio
├── serializers.py         # ✨ NOVO - Formatação de saída
├── services/              # Lógica de negócio
│   ├── __init__.py
│   ├── agent_service.py
│   ├── metrics_service.py
│   ├── alerts_service.py
│   └── ...
├── management/commands/   # Jobs
├── tests/                 # ✨ ORGANIZAR - Testes estruturados
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_services.py
│   └── ...
└── templates/app/         # Templates
```

### 10.3 Camadas e Responsabilidades

#### Models
- Apenas definição de dados
- Validações básicas de campo
- Métodos de instância simples
- Sem lógica de negócio complexa

#### Selectors
- Queries ORM reutilizáveis
- Filtros complexos
- Agregações
- Prefetch/select_related
- Retorna QuerySets ou listas

#### Services
- Lógica de negócio
- Orquestração de operações
- Transações
- Chamadas externas
- Retorna objetos de domínio

#### Forms
- Validação de entrada
- Limpeza de dados
- Mensagens de erro
- Widgets customizados

#### Validators
- Validações de domínio reutilizáveis
- Regras de negócio
- Pode ser usado em forms e models

#### Permissions
- Controle de acesso granular
- Reutilizável em views e templates
- Baseado em roles ou objetos

#### Serializers
- Formatação de saída
- Transformação de dados
- Preparação para templates ou API

#### Views
- Orquestração apenas
- Chama selectors, services, forms
- Prepara contexto para template
- Máximo 100-200 linhas por view

---

## 11. Riscos de Quebra

### 11.1 Riscos Baixos (Seguro)

✅ **Adicionar novas camadas**
- Criar `forms.py`, `permissions.py`, `selectors.py`
- Não quebra nada existente

✅ **Extrair métodos para services**
- Mover lógica de views para services
- Views continuam funcionando

✅ **Criar novas views/templates**
- Adicionar telas de configurações
- Admin continua funcionando

✅ **Adicionar testes**
- Organizar pasta `tests/`
- Não afeta código existente

### 11.2 Riscos Médios (Cuidado)

⚠️ **Refatorar views grandes**
- Quebrar `DashboardView` em partes
- Risco: mudar comportamento sem querer
- Mitigação: Testes antes e depois

⚠️ **Mudar queries ORM**
- Otimizar queries em selectors
- Risco: mudar resultados
- Mitigação: Comparar resultados antes/depois

⚠️ **Alterar models**
- Adicionar campos ou constraints
- Risco: migrations complexas
- Mitigação: Migrations reversíveis

### 11.3 Riscos Altos (Evitar)

❌ **Remover código sem análise**
- Pode ter dependências ocultas

❌ **Mudar assinaturas de métodos públicos**
- Pode quebrar templates ou outros apps

❌ **Alterar estrutura de dados retornados**
- Templates dependem da estrutura

❌ **Remover templates sem substituir**
- Quebra páginas

### 11.4 Estratégia de Mitigação

1. **Testes antes de refatorar**
   - Criar testes para comportamento atual
   - Garantir que refatoração não muda resultado

2. **Refatoração incremental**
   - Uma view por vez
   - Um service por vez
   - Commit pequenos e frequentes

3. **Feature flags**
   - Novas telas convivem com admin
   - Migração gradual de usuários

4. **Rollback plan**
   - Migrations reversíveis
   - Deploy com rollback rápido
   - Monitoramento de erros

---

## 12. Resumo Executivo

### 12.1 Pontos Fortes do Projeto

✅ **Arquitetura base sólida**
- Django bem configurado
- Apps separados por domínio
- Services já existem em alguns apps

✅ **App Assistant bem estruturado**
- Camada de services exemplar
- Testes unitários
- Observabilidade

✅ **Funcionalidades implementadas**
- Dashboards funcionais
- Monitoramento operacional
- Assistente IA

### 12.2 Problemas Críticos

❌ **Views gigantes**
- `monitoring/views.py` com 2368 linhas
- Responsabilidades misturadas
- Difícil manter e testar

❌ **Falta de camadas essenciais**
- Sem forms, permissions, selectors, validators
- Lógica espalhada
- Código duplicado

❌ **Dependência excessiva do admin**
- Configurações, mensagens, integrações apenas no admin
- UX ruim para usuários finais

❌ **Testes mal organizados**
- Arquivo único com 50k linhas
- Difícil navegar e manter

### 12.3 Impacto no Negócio

**Atual:**
- ⚠️ Difícil adicionar features
- ⚠️ Bugs difíceis de rastrear
- ⚠️ Onboarding lento de devs
- ⚠️ UX ruim para configurações

**Após Refatoração:**
- ✅ Features mais rápidas
- ✅ Código mais testável
- ✅ Manutenção mais fácil
- ✅ UX melhor para usuários

### 12.4 Recomendação

**Refatoração gradual e incremental** seguindo o plano de 5 etapas proposto no próximo documento.

**Não reescrever do zero.** O projeto tem base sólida, apenas precisa de organização e camadas adicionais.

---

## Próximos Passos

Consulte os documentos complementares:

1. **PROPOSTA_ORGANIZACAO_PASTAS.md** - Nova estrutura de pastas detalhada
2. **PLANO_REFATORACAO.md** - Plano de refatoração por etapas
3. **ARQUIVOS_PRIORIDADE.md** - Lista de arquivos a alterar primeiro

---

**Documento gerado automaticamente pela análise técnica do projeto.**  
**Nenhuma alteração foi feita no código durante esta análise.**
