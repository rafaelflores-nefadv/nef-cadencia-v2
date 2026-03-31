# 🏗️ Arquitetura

Estrutura e design do sistema NEF Cadencia v2.

## 📚 Documentos Disponíveis

### [ARCHITECTURE.md](./ARCHITECTURE.md)
Visão geral da arquitetura do sistema
- Diagrama de componentes
- Fluxo de dados
- Tecnologias utilizadas
- Decisões arquiteturais

### [BACKEND.md](./BACKEND.md)
Arquitetura do backend Django
- Estrutura de apps
- Models e relacionamentos
- Services e utils
- Padrões de código

### [DATABASE.md](./DATABASE.md)
Estrutura do banco de dados
- Tabelas principais
- Relacionamentos
- Índices e constraints
- Pipeline de dados

### [MULTITENANT.md](./MULTITENANT.md)
Sistema multi-tenant
- Workspaces
- Isolamento de dados
- Permissões por workspace
- Middleware

### [ESTRUTURA.md](./ESTRUTURA.md)
Organização de pastas e arquivos
- Estrutura de diretórios
- Convenções de nomenclatura
- Onde colocar cada tipo de arquivo

## 🎯 Conceitos Principais

### Apps Django

| App | Responsabilidade |
|-----|------------------|
| `accounts` | Autenticação, usuários, workspaces |
| `monitoring` | Monitoramento de agentes, dashboards |
| `assistant` | IA conversacional, tools |
| `messaging` | Templates de mensagens |
| `rules` | Configurações dinâmicas |
| `integrations` | Conectores externos |
| `reports` | Relatórios (futuro) |

### Pipeline de Dados

```
SQL Server Legado (LH)
    ↓
Importação/Sync (pyodbc)
    ↓
AgentEvent + AgentWorkday (bruto)
    ↓
rebuild_agent_day_stats
    ↓
AgentDayStats (agregado)
    ↓
Dashboard Views
    ↓
Templates + ApexCharts
```

### Camadas da Aplicação

1. **Apresentação:** Templates Django + Tailwind CSS
2. **Lógica de Negócio:** Views + Services
3. **Acesso a Dados:** Models + ORM
4. **Integrações:** pyodbc (SQL Server), OpenAI API

## 🔄 Fluxo de Requisição

```
Navegador
    ↓
URL (urls.py)
    ↓
View (views.py)
    ↓
Service (services/)
    ↓
Model (models.py)
    ↓
PostgreSQL
```

## 📦 Estrutura de Pastas

```
nef-cadencia-v2/
├── apps/                    # Apps Django
│   ├── accounts/
│   ├── monitoring/
│   ├── assistant/
│   └── ...
├── templates/               # Templates HTML
│   ├── base.html
│   ├── monitoring/
│   └── ...
├── static/                  # Arquivos estáticos
│   ├── css/
│   ├── js/
│   └── ...
├── docs/                    # Documentação
├── scripts/                 # Scripts utilitários
└── alive_platform/          # Configurações Django
    └── settings/
```

## 🛠️ Stack Técnica

- **Backend:** Django 4.2.x
- **Banco de Dados:** PostgreSQL 14+
- **Banco Legado:** SQL Server (via pyodbc)
- **Frontend:** Templates Django + Tailwind CSS
- **Gráficos:** ApexCharts
- **IA:** OpenAI API
- **Task Queue:** (futuro) Celery + Redis

## 📖 Leitura Recomendada

1. [ARCHITECTURE.md](./ARCHITECTURE.md) - Visão geral
2. [BACKEND.md](./BACKEND.md) - Detalhes do Django
3. [DATABASE.md](./DATABASE.md) - Estrutura de dados
4. [MULTITENANT.md](./MULTITENANT.md) - Multi-workspace
