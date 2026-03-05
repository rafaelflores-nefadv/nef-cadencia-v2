# Management Commands

Todos os comandos customizados atuais estao no app `monitoring`.

## Mapa rapido
| Comando | Finalidade |
| --- | --- |
| `check_legacy_connection` | valida conectividade com SQL Server legado e objetos principais |
| `sync_legacy_events` | sincronizacao incremental legado -> Agent/AgentEvent/AgentDayStats |
| `rebuild_agent_day_stats` | recalcula AgentDayStats por janela e opcionalmente por source |
| `import_lh_workday` | importa jornada diaria da `VW_LH_AGENT_WORKDAY` para `AgentWorkday` |
| `import_lh_pause_events` | importa pausas da `VW_LH_AGENT_PAUSE_EVENTS` para `AgentEvent` |
| `import_lh_all` | executa `import_lh_workday` + `import_lh_pause_events` |
| `import_lh_alive` | alias legado para `import_lh_all` |
| `wipe_lh_import` | remove dados `source="LH_ALIVE"` de `AgentEvent` e `AgentWorkday` |

## Filtros de data (imports e wipe)
Comandos com filtros compartilham estas flags:
- `--all`
- `--from YYYY-MM-DD --to YYYY-MM-DD`
- `--date YYYY-MM-DD`
- `--days N`
- `--today` (default)

Precedencia aplicada:
1. `--all`
2. `--from/--to`
3. `--date`
4. `--days`
5. `--today`

Regras:
- `--from` e `--to` devem ser usados juntos.
- `--from/--to` nao podem ser combinados com `--all`, `--date`, `--days` ou `--today`.

## 1) check_legacy_connection
Descricao:
Valida conexao ODBC e acessibilidade de:
- `TB_EVENTOS_LH_AGENTES`
- `VW_LH_AGENT_PAUSE_EVENTS`
- `VW_LH_AGENT_WORKDAY`

Uso:
```bash
python manage.py check_legacy_connection
```

Fluxo:
```text
Env LEGACY_* -> pyodbc.connect -> SELECT teste -> output SUCCESS/ERROR
```

## 2) sync_legacy_events
Descricao:
Sincroniza eventos de tabela legado em janela movel, recalculando stats diarios.

Parametros:
- `--lookback-minutes`
- `--dry-run`

Uso:
```bash
python manage.py sync_legacy_events
python manage.py sync_legacy_events --lookback-minutes 60
python manage.py sync_legacy_events --dry-run
```

Fluxo:
```text
SQL Server tabela legado
  -> normalize row
  -> upsert Agent
  -> upsert AgentEvent (source_event_hash)
  -> rebuild AgentDayStats
  -> JobRun (SUCCESS/ERROR)
```

## 3) import_lh_workday
Descricao:
Importa jornadas da view `VW_LH_AGENT_WORKDAY` para `AgentWorkday`.

Dedupe:
- `update_or_create(source="LH_ALIVE", cd_operador, work_date)`

Exemplos:
```bash
python manage.py import_lh_workday --today
python manage.py import_lh_workday --date 2026-03-05
python manage.py import_lh_workday --from 2026-01-01 --to 2026-01-31
python manage.py import_lh_workday --all
```

Fluxo:
```text
SQL Server view -> parsing + hms_to_seconds -> update_or_create -> AgentWorkday
```

## 4) rebuild_agent_day_stats
Descricao:
Recalcula agregacoes diarias (`AgentDayStats`) para um range.

Parametros:
- mesmos filtros de data (`--all`, `--from/--to`, `--date`, `--days`, `--today`)
- `--source` (opcional)

Exemplos:
```bash
python manage.py rebuild_agent_day_stats --today
python manage.py rebuild_agent_day_stats --from 2026-03-01 --to 2026-03-31 --source LH_ALIVE
python manage.py rebuild_agent_day_stats --all
```

## 5) import_lh_pause_events
Descricao:
Importa pausas da view `VW_LH_AGENT_PAUSE_EVENTS` para `AgentEvent`.

Dedupe:
- `update_or_create(source="LH_ALIVE", ext_event)`

Garantias:
- cria/atualiza `Agent` por `cd_operador` antes de gravar evento.

Exemplos:
```bash
python manage.py import_lh_pause_events --today
python manage.py import_lh_pause_events --from 2026-01-01 --to 2026-12-31
python manage.py import_lh_pause_events --all
```

Fluxo:
```text
SQL Server view -> parsing -> ensure Agent -> update_or_create AgentEvent
```

## 6) import_lh_all / import_lh_alive
Descricao:
Executa os dois imports em sequencia com as mesmas flags de filtro.

Uso:
```bash
python manage.py import_lh_all --today
python manage.py import_lh_all --all
python manage.py import_lh_alive --from 2026-01-01 --to 2026-01-31
```

## 7) wipe_lh_import
Descricao:
Rollback seguro dos dados importados do LH (`source="LH_ALIVE"`).

Escopo:
- `AgentWorkday` filtrado por `work_date`
- `AgentEvent` filtrado por `dt_inicio` (ou todos com `--all`)

Comportamento:
- mostra contagem antes de apagar
- pede confirmacao (`y/N`)
- `--force` evita prompt

Exemplos:
```bash
python manage.py wipe_lh_import --today
python manage.py wipe_lh_import --from 2026-01-01 --to 2026-01-31
python manage.py wipe_lh_import --all --force
```

## Progresso e observabilidade
- `import_lh_workday` e `import_lh_pause_events` usam `tqdm` com total explicito.
- Resumo final por contador: `created`, `updated`, `skipped`, `errors`.
