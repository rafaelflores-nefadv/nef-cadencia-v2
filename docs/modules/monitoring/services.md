# Monitoring - Services

## `legacy_sync_service.py`
Servico para sincronizacao incremental de eventos legados.

Responsabilidades:
- conectar ao SQL Server legado
- consultar eventos por janela movel (`lookback`)
- normalizar payloads
- upsert de `Agent` e `AgentEvent` por hash
- recalcular `AgentDayStats` para pares afetados

Ponto de entrada:
- `LegacySyncService.run()`

Saida:
- dicionario com contadores (`agents_upserted`, `events_created`, etc.)

## `lh_import_utils.py`
Utilitarios compartilhados pelos comandos de import LH.

Funcoes chave:
- `add_date_filter_arguments(parser)`
- `resolve_date_window(options)`
- `connect_legacy()`
- `get_legacy_schema()`
- `fetch_rows(...)`
- conversores (`to_date`, `to_aware_datetime`, `to_bigint`, etc.)
- `hms_to_seconds` (importado de `monitoring.utils`)

### `connect_legacy`
Funcao central para conexao com SQL Server:
- valida env vars `LEGACY_*`
- monta connection string ODBC
- retorna conexao `pyodbc`

## `day_stats_service.py`
Servico de consolidacao diaria para `AgentDayStats`.

Funcoes chave:
- `rebuild_agent_day_stats(date_from, date_to, source=None)`
- `infer_rebuild_window_for_all(source=None)`

Comportamento:
- agrega eventos por agente/dia (pausas, logon, logoff)
- inclui pares de dia vindos de `AgentWorkday` para nao perder atividade sem pausa
- cria/atualiza `AgentDayStats` de forma idempotente

Uso:
- chamado automaticamente ao final dos imports LH
- pode ser acionado manualmente via comando:
  - `python manage.py rebuild_agent_day_stats --today`
  - `python manage.py rebuild_agent_day_stats --from 2026-03-01 --to 2026-03-31 --source LH_ALIVE`

## `utils.py` (apoio)
Funcoes utilitarias de formatacao e conversao de tempo:
- `hms_to_seconds`
- formatadores para exibicao de duracao no dashboard/runs

## Dependencias
- `pyodbc` para legado
- `django.utils.timezone` para padronizacao temporal
- models `Agent`, `AgentEvent`, `AgentDayStats`, `AgentWorkday`
