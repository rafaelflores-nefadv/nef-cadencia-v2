# Monitoring - Management Commands

## Comandos disponiveis
- `check_legacy_connection`
- `sync_legacy_events`
- `rebuild_agent_day_stats`
- `import_lh_workday`
- `import_lh_pause_events`
- `import_lh_all`
- `import_lh_alive` (alias)
- `wipe_lh_import`

## Quando usar cada comando
### `check_legacy_connection`
Validacao rapida de conectividade ODBC com objetos LH.

### `import_lh_workday`
Importa jornada diaria da view `VW_LH_AGENT_WORKDAY` para `AgentWorkday`.

### `import_lh_pause_events`
Importa pausas da view `VW_LH_AGENT_PAUSE_EVENTS` para `AgentEvent`.

### `import_lh_all`
Executa em sequencia: `import_lh_workday` + `import_lh_pause_events`.

### `import_lh_alive`
Alias legado para `import_lh_all`.

### `sync_legacy_events`
Sync incremental de tabela legado (janela movel), com atualizacao de `AgentDayStats`.

### `rebuild_agent_day_stats`
Reconstrucao segura de agregados diarios (`AgentDayStats`) por janela.

### `wipe_lh_import`
Rollback controlado dos dados importados do LH (`source="LH_ALIVE"`) em bruto.

## Filtros de data
Comandos de import/wipe/rebuild compartilham:
- `--all`
- `--from YYYY-MM-DD --to YYYY-MM-DD`
- `--date YYYY-MM-DD`
- `--days N`
- `--today` (padrao)

Precedencia:
1. `--all`
2. `--from/--to`
3. `--date`
4. `--days`
5. `--today`

## Exemplos de uso
### Importacao LH
```bash
python manage.py import_lh_pause_events --date 2026-03-05
python manage.py import_lh_workday --date 2026-03-05
python manage.py import_lh_all --date 2026-03-05
```

### Rebuild de stats
```bash
python manage.py rebuild_agent_day_stats --date 2026-03-05 --source LH_ALIVE
python manage.py rebuild_agent_day_stats --from 2026-03-01 --to 2026-03-31 --source LH_ALIVE
```

### Wipe controlado
```bash
python manage.py wipe_lh_import --date 2026-03-05
python manage.py wipe_lh_import --from 2026-03-01 --to 2026-03-31 --force
```

## Protecao de tabelas brutas
`AgentEvent` e `AgentWorkday` sao write-protected por padrao.

Somente comandos oficiais de ingestao/sync/wipe podem escrever/apagar nessas tabelas.

Fora desses comandos:
- ORM falha com `PermissionDenied`
- shell/admin/script manual nao deve ser usado para dado bruto
