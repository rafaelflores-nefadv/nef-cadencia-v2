# Arquitetura do Sistema

## Contexto
Aplicacao Django monolitica modular, com separacao por apps de dominio.

Camadas logicas:
- apresentacao: views/templates/endpoints
- aplicacao: services e management commands
- persistencia: PostgreSQL
- integracao externa: SQL Server legado + OpenAI + canais

## Composicao por apps
| App | Papel principal | Dados proprietarios |
| --- | --- | --- |
| `accounts` | autenticacao e UX de acesso | auth padrao |
| `monitoring` | ingestao LH, BI operacional, risco, alertas | `Agent`, `AgentEvent`, `AgentWorkday`, `AgentDayStats`, `PauseClassification`, `JobRun`, `Notification*` |
| `rules` | parametros dinamicos | `SystemConfig` |
| `messaging` | templates | `MessageTemplate` |
| `integrations` | conectores/canais | `Integration` |
| `assistant` | chat e tool-calling | `AssistantConversation`, `AssistantMessage`, `AssistantActionLog` |
| `reports` | reservado | sem modelos ativos |

## Pipeline de dados do monitoring
```text
SQL Server (LH)
   |
   | import_lh_pause_events / import_lh_workday / import_lh_all / import_lh_alive
   | sync_legacy_events
   v
AgentEvent + AgentWorkday   (bruto)
   |
   | rebuild_agent_day_stats
   v
AgentDayStats               (agregado)
   |
   v
Dashboard operacional
```

## Rotas principais
- `/dashboard`
- `/dashboard/day-detail`
- `/agents`, `/agents/<id>`
- `/runs`, `/runs/<id>`
- `/admin/monitoring/pause-classification`
- `/assistant/chat`
- `/admin/`

## Blindagem de tabelas brutas
`AgentEvent` e `AgentWorkday` sao protegidas por guard rail no ORM.

Principio:
- mutacao fora de comandos oficiais de ingestao/sync/wipe resulta em `PermissionDenied`
- admin para bruto e readonly

## Classificacao de pausas e risco
- classificacao tecnica: `LEGAL`, `NEUTRAL`, `HARMFUL`, `UNCLASSIFIED`
- nomenclatura operacional no frontend:
  - Tempo Produtivo
  - Tempo Neutro
  - Tempo Improdutivo
  - Tempo Nao Classificado
- score de risco centralizado em `apps/monitoring/services/risk_scoring.py`

## Principios de projeto
- idempotencia de importacao por constraints + upsert
- rastreabilidade em `raw_payload`
- separacao entre bruto e agregado
- recuperacao operacional via comando (sem manipular bruto manualmente)
