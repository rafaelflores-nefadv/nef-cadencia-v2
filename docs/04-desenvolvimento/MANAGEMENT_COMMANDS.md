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

## Filtros de data (imports, wipe e rebuild)
Comandos com filtro compartilham:
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

## 1) `check_legacy_connection`
Valida conexao ODBC e leitura de objetos criticos do LH.

Uso:
```bash
python manage.py check_legacy_connection
```

## 2) `sync_legacy_events`
Sync incremental da tabela legado em janela movel.

Uso:
```bash
python manage.py sync_legacy_events
python manage.py sync_legacy_events --lookback-minutes 60
python manage.py sync_legacy_events --dry-run
```

Fluxo:
```text
LEGACY_EVENTS_TABLE
  -> normalize row
  -> upsert Agent
  -> upsert AgentEvent
  -> rebuild AgentDayStats
  -> JobRun
```

## 3) `import_lh_workday`
Importa jornada da `VW_LH_AGENT_WORKDAY` para `AgentWorkday`.

Uso:
```bash
python manage.py import_lh_workday --today
python manage.py import_lh_workday --date 2026-03-05
python manage.py import_lh_workday --from 2026-03-01 --to 2026-03-31
python manage.py import_lh_workday --all
```

## 4) `import_lh_pause_events`
Importa pausas da `VW_LH_AGENT_PAUSE_EVENTS` para `AgentEvent`.

Uso:
```bash
python manage.py import_lh_pause_events --today
python manage.py import_lh_pause_events --date 2026-03-05
python manage.py import_lh_pause_events --from 2026-03-01 --to 2026-03-31
python manage.py import_lh_pause_events --all
```

## 5) `import_lh_all` / `import_lh_alive`
Executa os dois imports em sequencia, com os mesmos filtros.

Uso:
```bash
python manage.py import_lh_all --date 2026-03-05
python manage.py import_lh_all --all
python manage.py import_lh_alive --from 2026-03-01 --to 2026-03-31
```

## 6) `rebuild_agent_day_stats`
Reconstrucao de `AgentDayStats` por janela.

Uso:
```bash
python manage.py rebuild_agent_day_stats --date 2026-03-05
python manage.py rebuild_agent_day_stats --from 2026-03-01 --to 2026-03-31
python manage.py rebuild_agent_day_stats --date 2026-03-05 --source LH_ALIVE
python manage.py rebuild_agent_day_stats --all
```

Quando usar:
- apos importacao LH para recompor agregados
- quando houver inconsistencia entre bruto e dashboard
- em manutencao historica de periodo

## 7) `wipe_lh_import`
Rollback controlado de bruto LH (`source="LH_ALIVE"`).

Comportamento:
- conta registros antes de apagar
- pede confirmacao (`y/N`)
- `--force` evita prompt

Uso:
```bash
python manage.py wipe_lh_import --date 2026-03-05
python manage.py wipe_lh_import --from 2026-03-01 --to 2026-03-31 --force
python manage.py wipe_lh_import --all --force
```

## Blindagem de tabelas brutas
`AgentEvent` e `AgentWorkday` possuem guard rail de mutacao.

Fora de ambiente de teste, mutacao ORM nessas tabelas so e permitida nos comandos oficiais:
- `import_lh_pause_events`
- `import_lh_workday`
- `import_lh_all`
- `import_lh_alive`
- `sync_legacy_events`
- `wipe_lh_import`

Fora desses fluxos:
- `PermissionDenied`
- shell/admin/script manual nao deve ser usado para dado bruto

## Operacao via Dashboard
Na dashboard (usuarios `is_staff`):
- botao **Gerar stats do dia** chama rebuild de stats para a data
- botoes de copia para importacao do dia:
  - `python manage.py import_lh_pause_events --date YYYY-MM-DD`
  - `python manage.py import_lh_workday --date YYYY-MM-DD`

## Recuperacao do monitoring em caso de problema
Passo a passo recomendado:

1. Reimportar bruto LH do periodo
```bash
python manage.py import_lh_workday --date YYYY-MM-DD
python manage.py import_lh_pause_events --date YYYY-MM-DD
# ou
python manage.py import_lh_all --date YYYY-MM-DD
```

2. Rebuild de agregados diarios
```bash
python manage.py rebuild_agent_day_stats --date YYYY-MM-DD --source LH_ALIVE
```

3. Validar contagens
- bruto: `AgentEvent` e `AgentWorkday`
- agregado: `AgentDayStats`

4. Validar dashboard
- abrir `/dashboard?data_ref=YYYY-MM-DD`
- conferir cards, rankings, risco e alertas

## Progresso e observabilidade
- imports LH exibem contadores `created`, `updated`, `skipped`, `errors`
- jobs criticos gravam historico em `JobRun`
