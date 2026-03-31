# NEF Cadencia v2 - Documentação Técnica

## 📋 Índice Geral

### 🚀 [1. Início Rápido](./01-inicio/)
Guias para começar a usar o sistema
- [Instalação Linux](./01-inicio/INSTALL_LINUX.md)
- [Configuração Inicial](./01-inicio/CONFIGURACAO.md)
- [Setup do Banco de Dados](./01-inicio/SETUP_DATABASE.md)
- [Variáveis de Ambiente](./01-inicio/VARIAVEIS_AMBIENTE.md)

### 🏗️ [2. Arquitetura](./02-arquitetura/)
Estrutura e design do sistema
- [Visão Geral da Arquitetura](./02-arquitetura/ARCHITECTURE.md)
- [Backend Django](./02-arquitetura/BACKEND.md)
- [Banco de Dados](./02-arquitetura/DATABASE.md)
- [Multi-tenant](./02-arquitetura/MULTITENANT.md)
- [Estrutura de Pastas](./02-arquitetura/ESTRUTURA.md)

### 📦 [3. Módulos](./03-modulos/)
Documentação por módulo do sistema
- [Monitoring](./03-modulos/monitoring/)
- [Assistant (IA)](./03-modulos/assistant/)
- [Messaging](./03-modulos/messaging/)
- [Rules](./03-modulos/rules/)
- [Integrations](./03-modulos/integrations/)
- [Accounts](./03-modulos/accounts/)

### 🔧 [4. Desenvolvimento](./04-desenvolvimento/)
Guias para desenvolvedores
- [Comandos de Gerenciamento](./04-desenvolvimento/MANAGEMENT_COMMANDS.md)
- [Testes](./04-desenvolvimento/TESTES.md)
- [API e Autenticação](./04-desenvolvimento/API_AUTH.md)
- [Sistema de Permissões](./04-desenvolvimento/PERMISSOES.md)

### 🎨 [5. Frontend](./05-frontend/)
Interface e experiência do usuário
- [Guia Visual](./05-frontend/GUIA_VISUAL.md)
- [Integração Frontend-Backend](./05-frontend/INTEGRACAO.md)
- [Navegação e Rotas](./05-frontend/NAVEGACAO.md)

### 🚢 [6. Deploy](./06-deploy/)
Implantação e produção
- [Deploy em VPS](./06-deploy/DEPLOY_VPS.md)
- [Fluxo de Deploy](./06-deploy/FLUXO_DEPLOY.md)
- [Checklist de Produção](./06-deploy/CHECKLIST_PRODUCAO.md)
- [Política de Segredos](./06-deploy/POLITICA_SEGREDOS.md)

### ✨ [7. Melhorias](./07-melhorias/)
Atualizações e novos recursos
- [Melhorias Visuais e Dados Fictícios](./07-melhorias/VISUAL_E_MOCK_DATA.md)
- [Refatorações Implementadas](./07-melhorias/REFATORACOES.md)
- [Reorganização Frontend](./07-melhorias/REORGANIZACAO_FRONTEND.md)

### 📊 [8. Análises](./08-analises/)
Diagnósticos e auditorias
- [Análise Completa do Projeto](./08-analises/ANALISE_COMPLETA.md)
- [Diagnóstico Técnico](./08-analises/DIAGNOSTICO_TECNICO.md)
- [Auditoria de Produção](./08-analises/AUDITORIA_PRODUCAO.md)
- [Riscos de Quebra](./08-analises/RISCOS_QUEBRA.md)

---

## 🎯 Objetivo da Plataforma

O **NEF Cadencia v2** é uma plataforma Django para:
- Monitoramento operacional de agentes
- Ingestão de dados do legado LH
- Aplicação de regras dinâmicas
- Notificações assistidas por IA
- Dashboards executivos e operacionais

## 🛠️ Stack Técnica

- **Backend:** Django 4.2.x
- **Banco Principal:** PostgreSQL
- **Banco Legado:** SQL Server via `pyodbc`
- **IA:** OpenAI API
- **Frontend:** Templates Django + Tailwind CSS
- **Gráficos:** ApexCharts

## 📱 Apps Django

| App | Responsabilidade |
|-----|------------------|
| `accounts` | Autenticação e contexto de menu |
| `monitoring` | Ingestão LH, stats diários, dashboard, risco, alertas |
| `rules` | Configuração dinâmica (`SystemConfig`) |
| `messaging` | Templates de mensagens |
| `integrations` | Configurações de conectores |
| `assistant` | API de chat e tools IA |
| `reports` | Relatórios (reservado) |

## 🔄 Pipeline de Dados

```
SQL Server (Legado)
    ↓
Importação/Sync
    ↓
AgentEvent + AgentWorkday (bruto)
    ↓
rebuild_agent_day_stats
    ↓
AgentDayStats (agregado)
    ↓
Dashboard
```

## 📖 Leitura Recomendada (Ordem)

1. **Começando:** [Instalação Linux](./01-inicio/INSTALL_LINUX.md)
2. **Entendendo:** [Arquitetura](./02-arquitetura/ARCHITECTURE.md)
3. **Usando:** [Comandos](./04-desenvolvimento/MANAGEMENT_COMMANDS.md)
4. **Desenvolvendo:** [Módulo Monitoring](./03-modulos/monitoring/)
5. **Implantando:** [Deploy VPS](./06-deploy/DEPLOY_VPS.md)

## 🆘 Precisa de Ajuda?

- **Instalação:** Ver [01-inicio/](./01-inicio/)
- **Erros de Deploy:** Ver [06-deploy/CHECKLIST_PRODUCAO.md](./06-deploy/CHECKLIST_PRODUCAO.md)
- **Comandos:** Ver [04-desenvolvimento/MANAGEMENT_COMMANDS.md](./04-desenvolvimento/MANAGEMENT_COMMANDS.md)
- **Dados Fictícios:** Ver [07-melhorias/VISUAL_E_MOCK_DATA.md](./07-melhorias/VISUAL_E_MOCK_DATA.md)
