# Monitoring - Management Commands

## Lista de comandos
- `check_legacy_connection`
- `sync_legacy_events`
- `rebuild_agent_day_stats`
- `import_lh_workday`
- `import_lh_pause_events`
- `import_lh_all`
- `import_lh_alive` (alias legado)
- `wipe_lh_import`

## `import_lh_workday`
Descricao:
- Importa `VW_LH_AGENT_WORKDAY` para `AgentWorkday`.

Dedupe:
- `update_or_create(source="LH_ALIVE", cd_operador, work_date)`

Progresso:
- barra `tqdm` com total explicito e contadores.

## `import_lh_pause_events`
Descricao:
- Importa `VW_LH_AGENT_PAUSE_EVENTS` para `AgentEvent`.

Dedupe:
- `update_or_create(source="LH_ALIVE", ext_event)`

Garantias:
- cria/atualiza `Agent` por `cd_operador` antes de gravar evento.

## `import_lh_all`
Descricao:
- Executa `import_lh_workday` e `import_lh_pause_events` em sequencia.

## `import_lh_alive`
Descricao:
- Compatibilidade retroativa, encaminha para `import_lh_all`.

## `wipe_lh_import`
Descricao:
- Remove registros `source="LH_ALIVE"` em `AgentEvent` e `AgentWorkday`.
- Mostra contagem previa.
- Requer confirmacao (ou `--force`).

## `sync_legacy_events`
Descricao:
- Sync incremental da tabela legado (janela movel), com `JobRun`.

## `rebuild_agent_day_stats`
Descricao:
- Recalcula `AgentDayStats` para uma janela.
- Suporta filtro opcional por `--source`.

Exemplos:
- `python manage.py rebuild_agent_day_stats --today`
- `python manage.py rebuild_agent_day_stats --from 2026-03-01 --to 2026-03-31 --source LH_ALIVE`
- `python manage.py rebuild_agent_day_stats --all`

## `check_legacy_connection`
Descricao:
- Valida credenciais ODBC e leitura de tabela/views criticas do LH.

## Filtros suportados
Comandos de import e wipe usam:
- `--all`
- `--from ... --to ...`
- `--date ...`
- `--days ...`
- `--today` (default)

Precedencia:
- `--all` > `--from/--to` > `--date` > `--days` > `--today`
