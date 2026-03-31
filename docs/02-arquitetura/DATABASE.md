# Banco de Dados

## Banco principal (PostgreSQL)
Configurado em `alive_platform/settings.py` (`DATABASES['default']`).

## Tabelas do monitoring
### Brutas de ingestao LH
- `AgentEvent`
- `AgentWorkday` (`monitoring_agent_workday`)

### Agregada diaria
- `AgentDayStats`

### Suporte operacional
- `Agent`
- `PauseClassification`
- `NotificationHistory`
- `NotificationThrottle`
- `JobRun`

## Regras de dedupe e integridade
### `AgentEvent`
- unico `(source, source_event_hash)`
- unico parcial `(source, ext_event)` quando `ext_event` nao nulo
- check de `duracao_seg` nao negativa

### `AgentWorkday`
- unico `(source, cd_operador, work_date)`
- unico `(source, ext_event)`

### `PauseClassification`
- unico ativo por `(source, pause_name_normalized)`

## Pipeline de persistencia
```text
SQL Server (origem)
  -> import/sync
  -> AgentEvent + AgentWorkday (bruto)
  -> rebuild_agent_day_stats
  -> AgentDayStats (agregado)
```

## Blindagem de bruto
`AgentEvent` e `AgentWorkday` sao write-protected por padrao no ORM.

Apenas comandos oficiais mutam bruto:
- `import_lh_pause_events`
- `import_lh_workday`
- `import_lh_all`
- `import_lh_alive`
- `sync_legacy_events`
- `wipe_lh_import`

Fora desses fluxos, ocorre `PermissionDenied`.

## Banco legado (SQL Server - LH)
A aplicacao so le do legado:
- `LEGACY_EVENTS_TABLE` (sync incremental)
- `VW_LH_AGENT_PAUSE_EVENTS`
- `VW_LH_AGENT_WORKDAY`
- `TB_EVENTOS_LH_AGENTES` (check de conectividade)

Conexao via `pyodbc` e env vars `LEGACY_*`.

## Recomendacoes de manutencao
- nao inserir dado manual em bruto
- usar `wipe_lh_import` para rollback de bruto LH
- apos import/reprocessamento, executar `rebuild_agent_day_stats`
- validar dashboard por data (`/dashboard?data_ref=YYYY-MM-DD`)
