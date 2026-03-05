# Sync de Eventos do Legado

## Objetivo

O comando `sync_legacy_events` faz a sincronizacao incremental dos eventos do legado para:

- `monitoring.Agent`
- `monitoring.AgentEvent`
- `monitoring.AgentDayStats`
- `monitoring.JobRun` (execucao do comando)

Estrategia aplicada: **janela movel + dedupe por hash**, permitindo execucao recorrente sem duplicar dados.

## Configuracao de ambiente

No arquivo `.env`, configure a conexao com o legado:

```env
LEGACY_DRIVER=ODBC Driver 18 for SQL Server
LEGACY_SERVER=127.0.0.1
LEGACY_PORT=1433
LEGACY_USER=sa
LEGACY_PASSWORD=change-me
LEGACY_DATABASE=legacy_db
LEGACY_SCHEMA=dbo
```

Opcional:

```env
LEGACY_EVENTS_TABLE=agent_events
```

## Configuracoes em `SystemConfig`

O comando usa (e, fora de dry-run, cria defaults caso nao existam):

- `SYNC_LOOKBACK_MINUTES` (int, default `180`)
- `LEGACY_SOURCE_NAME` (string, default `legacy`)
- `LEGACY_ENABLED` (bool, default `true`)

## Como executar

Execucao padrao:

```bash
python manage.py sync_legacy_events
```

Sobrescrevendo janela:

```bash
python manage.py sync_legacy_events --lookback-minutes 60
```

Dry-run (nao grava no banco local):

```bash
python manage.py sync_legacy_events --dry-run
```

## Comportamento

- Busca no legado somente `LOGON`, `LOGOFF` e `PAUSA` dentro da janela.
- Gera `source_event_hash` com:
  - `source|cd_operador|tp_evento|nm_pausa|dt_inicio_iso`
- Faz upsert de `Agent` por `cd_operador`.
- Faz upsert idempotente de `AgentEvent` por `(source, source_event_hash)`.
- Recalcula `AgentDayStats` apenas para pares `agente + dia` afetados.
- Registra `JobRun` com `RUNNING`, `SUCCESS` ou `ERROR`, incluindo resumo e stack trace em erro.
