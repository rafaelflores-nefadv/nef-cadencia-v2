# Modulo Monitoring

## Escopo
Dominio operacional do sistema: agentes, eventos, estatisticas, notificacoes e execucoes de jobs.

## Models (`apps/monitoring/models.py`)
- `Agent`
- `AgentEvent`
- `AgentDayStats`
- `NotificationHistory`
- `NotificationThrottle`
- `JobRun`

## Views e paginas
- `DashboardView` -> `/dashboard`
- `AgentListView` -> `/agents`
- `AgentDetailView` -> `/agents/<id>`
- `JobRunListView` -> `/runs`
- `JobRunDetailView` -> `/runs/<id>`

Todas as views usam `LoginRequiredMixin`.

## Servicos
- `apps/monitoring/services/legacy_sync_service.py`
  - consulta fonte legada (ODBC)
  - normaliza e deduplica eventos por hash
  - upsert de agente/evento
  - recalculo de estatisticas diarias afetadas

## Management command
- `python manage.py sync_legacy_events`
  - arquivo: `apps/monitoring/management/commands/sync_legacy_events.py`
  - registra `JobRun` com status `RUNNING/SUCCESS/ERROR`

## Integracao com assistente
- Tools de leitura usam:
  - `AgentDayStats` (ranking/resumo)
  - `AgentEvent` (pausas atuais)
  - `Agent` (dados do agente)
- Tools de acao registram envio em `NotificationHistory`.

## Admin
Registrados:
- `Agent`
- `AgentEvent`
- `AgentDayStats`
- `NotificationHistory`
- `NotificationThrottle`
- `JobRun`
