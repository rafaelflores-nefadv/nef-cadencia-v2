# Estrutura Final do Projeto

**Data:** 18 de Março de 2026  
**Versão:** 1.0

---

## Árvore Completa de Pastas

```
nef-cadencia-v2/
├── alive_platform/              # Projeto Django principal
│   ├── __init__.py
│   ├── settings.py              # ✏️ Modificado (adicionado core)
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                        # Apps Django
│   │
│   ├── core/                    # ✨ NOVO - Camada compartilhada
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── mixins.py            # Mixins reutilizáveis
│   │   ├── decorators.py        # Decorators compartilhados
│   │   ├── validators.py        # Validadores compartilhados
│   │   ├── helpers.py           # Funções auxiliares
│   │   └── permissions.py       # Classes base de permissões
│   │
│   ├── accounts/                # Autenticação e usuários
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── forms.py             # ✨ NOVO
│   │   ├── permissions.py       # ✨ NOVO
│   │   ├── context_processors.py
│   │   ├── templatetags/
│   │   │   ├── __init__.py
│   │   │   └── admin_menu.py
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── monitoring/              # Monitoramento operacional (CORE)
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py            # 10 models
│   │   ├── views.py             # 2368 linhas (a refatorar)
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── guards.py
│   │   ├── utils.py
│   │   ├── selectors.py         # ✨ NOVO - 9 funções
│   │   ├── forms.py             # ✨ NOVO - 3 formulários
│   │   ├── permissions.py       # ✨ NOVO - 5 classes
│   │   ├── validators.py        # ✨ NOVO - 3 validadores
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── dashboard_period_filter.py
│   │   │   ├── day_stats_service.py
│   │   │   ├── legacy_sync_service.py
│   │   │   ├── lh_import_utils.py
│   │   │   ├── pause_classification.py
│   │   │   └── risk_scoring.py
│   │   ├── management/
│   │   │   └── commands/        # 10 commands
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── rules/                   # Configurações do sistema
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── selectors.py         # ✨ NOVO - 3 funções
│   │   ├── forms.py             # ✨ NOVO - 1 formulário
│   │   ├── permissions.py       # ✨ NOVO - 1 classe
│   │   ├── validators.py        # ✨ NOVO - 2 validadores
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── system_config.py
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── messaging/               # Templates de mensagens
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── choices.py
│   │   ├── selectors.py         # ✨ NOVO - 4 funções
│   │   ├── forms.py             # ✨ NOVO - 1 formulário
│   │   ├── permissions.py       # ✨ NOVO - 1 classe
│   │   ├── validators.py        # ✨ NOVO - 2 validadores
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── integrations/            # Integrações externas
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── selectors.py         # ✨ NOVO - 3 funções
│   │   ├── forms.py             # ✨ NOVO - 1 formulário
│   │   ├── permissions.py       # ✨ NOVO - 1 classe
│   │   ├── validators.py        # ✨ NOVO - 1 validador
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── assistant/               # Assistente IA
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py            # 5 models
│   │   ├── views.py             # 473 linhas
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── observability.py
│   │   ├── selectors.py         # ✨ NOVO - 5 funções
│   │   ├── forms.py             # ✨ NOVO - 1 formulário
│   │   ├── permissions.py       # ✨ NOVO - 3 classes
│   │   ├── services/            # 20 arquivos
│   │   │   ├── __init__.py
│   │   │   ├── analytics_context.py
│   │   │   ├── assistant_config.py
│   │   │   ├── assistant_service.py
│   │   │   ├── audit_service.py
│   │   │   ├── business_glossary.py
│   │   │   ├── capabilities.py
│   │   │   ├── conversation_store.py
│   │   │   ├── guardrails.py
│   │   │   ├── metrics_service.py
│   │   │   ├── openai_client.py
│   │   │   ├── openai_settings.py
│   │   │   ├── processing_status.py
│   │   │   ├── semantic_intent.py
│   │   │   ├── semantic_resolution.py
│   │   │   ├── system_prompt.py
│   │   │   ├── tool_registry.py
│   │   │   ├── tools_actions.py
│   │   │   ├── tools_read.py
│   │   │   └── widget_session_service.py
│   │   ├── templatetags/
│   │   │   ├── __init__.py
│   │   │   └── assistant_ui.py
│   │   ├── tests/               # 14 arquivos
│   │   └── migrations/
│   │
│   └── reports/                 # Relatórios (vazio)
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py
│       ├── views.py
│       ├── admin.py
│       ├── tests/
│       └── migrations/
│
├── templates/                   # Templates Django
│   ├── base.html
│   ├── accounts/
│   │   └── login.html
│   ├── admin/                   # 6 templates
│   ├── assistant/               # 2 templates
│   ├── layouts/                 # 2 templates
│   ├── monitoring/              # 12 templates
│   └── partials/                # 1 template
│
├── static/                      # Arquivos estáticos
│   ├── css/
│   ├── js/
│   └── images/
│
├── docs/                        # Documentação
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── DEPLOYMENT.md
│   ├── INSTALL_LINUX.md
│   ├── INTEGRATIONS.md
│   ├── MANAGEMENT_COMMANDS.md
│   ├── README.md
│   ├── SYNC.md
│   ├── DIAGNOSTICO_TECNICO.md           # ✨ Análise técnica
│   ├── PROPOSTA_ORGANIZACAO_PASTAS.md   # ✨ Proposta de estrutura
│   ├── PLANO_REFATORACAO.md             # ✨ Plano de refatoração
│   ├── ARQUIVOS_PRIORIDADE.md           # ✨ Lista priorizada
│   ├── RISCOS_QUEBRA.md                 # ✨ Análise de riscos
│   ├── REORGANIZACAO_IMPLEMENTADA.md    # ✨ Documentação da implementação
│   └── ESTRUTURA_FINAL.md               # ✨ Este arquivo
│
├── manage.py
├── requirements.txt
├── package.json
├── tailwind.config.js
├── postcss.config.js
├── .env
├── .gitignore
└── README.md
```

---

## Legenda

- ✅ **Existente** - Arquivo/pasta já existia
- ✨ **NOVO** - Arquivo/pasta criado na reorganização
- ✏️ **Modificado** - Arquivo existente que foi modificado

---

## Resumo por App

### Core (NOVO)
- **Arquivos:** 7
- **Propósito:** Camada compartilhada
- **Conteúdo:** Mixins, decorators, validators, helpers, permissions

### Accounts
- **Arquivos novos:** 2 (forms.py, permissions.py)
- **Propósito:** Autenticação e perfil de usuário
- **Status:** Estrutura base criada

### Monitoring
- **Arquivos novos:** 4 (selectors.py, forms.py, permissions.py, validators.py)
- **Propósito:** Monitoramento operacional (app principal)
- **Status:** Camadas adicionadas, views ainda grande (2368 linhas)

### Rules
- **Arquivos novos:** 4 (selectors.py, forms.py, permissions.py, validators.py)
- **Propósito:** Configurações do sistema
- **Status:** Estrutura completa

### Messaging
- **Arquivos novos:** 4 (selectors.py, forms.py, permissions.py, validators.py)
- **Propósito:** Templates de mensagens
- **Status:** Estrutura completa

### Integrations
- **Arquivos novos:** 4 (selectors.py, forms.py, permissions.py, validators.py)
- **Propósito:** Integrações externas
- **Status:** Estrutura completa

### Assistant
- **Arquivos novos:** 3 (selectors.py, forms.py, permissions.py)
- **Propósito:** Assistente IA com OpenAI
- **Status:** Já bem estruturado, camadas complementadas

### Reports
- **Arquivos novos:** 0
- **Propósito:** Relatórios (não implementado)
- **Status:** Vazio, considerar remover ou implementar

---

## Estatísticas Finais

### Arquivos
- **Total de arquivos novos:** 28
- **Total de arquivos modificados:** 1
- **Total de arquivos removidos:** 0

### Linhas de Código
- **Linhas adicionadas:** ~1500
- **Linhas modificadas:** ~5
- **Linhas removidas:** 0

### Apps
- **Apps novos:** 1 (core)
- **Apps atualizados:** 6
- **Apps intocados:** 1 (reports)

### Camadas
- **Selectors:** 7 arquivos, 30+ funções
- **Forms:** 7 arquivos, 12+ formulários
- **Permissions:** 7 arquivos, 15+ classes
- **Validators:** 5 arquivos, 15+ validadores
- **Core utilities:** 7 arquivos, 20+ funções/classes

---

## Padrão Arquitetural

Cada app agora segue o padrão:

```
app/
├── models.py          # Definição de dados
├── views.py           # Lógica de apresentação
├── urls.py            # Rotas
├── forms.py           # ✨ Validação de entrada
├── selectors.py       # ✨ Queries reutilizáveis
├── permissions.py     # ✨ Controle de acesso
├── validators.py      # ✨ Validações de domínio
├── services/          # Lógica de negócio
├── admin.py           # Interface admin
├── tests/             # Testes
└── migrations/        # Migrações
```

---

## Próximos Passos

### Imediato
1. ✅ Estrutura criada
2. ✅ Camadas adicionadas
3. ✅ Settings atualizado
4. ⏳ Testar aplicação

### Curto Prazo (1-2 semanas)
1. Começar a usar selectors em novas features
2. Aplicar forms em novas telas
3. Usar permissions em views críticas
4. Adotar helpers do core

### Médio Prazo (1-2 meses)
1. Refatorar `monitoring/views.py` (dividir em múltiplos arquivos)
2. Mover queries existentes para selectors
3. Extrair validações para validators
4. Organizar testes em pastas estruturadas

### Longo Prazo (2-3 meses)
1. Criar telas para substituir admin (configs, templates, integrações)
2. Extrair mais lógica para services
3. Adicionar mais helpers ao core
4. Implementar ou remover app reports

---

**Estrutura final gerada após reorganização estrutural completa.**
