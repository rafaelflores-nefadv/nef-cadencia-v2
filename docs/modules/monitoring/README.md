# Modulo Monitoring

## Responsabilidade
`monitoring` e o nucleo operacional da plataforma.

Ele concentra:
- entidades de agentes, eventos e jornada
- agregacoes diarias para dashboard
- historico de notificacoes
- controle de execucao de jobs
- comandos de import/sync/rollback com legado
- rebuild dedicado de `AgentDayStats` para ranges historicos

## Componentes do modulo
- [models.md](./models.md)
- [services.md](./services.md)
- [commands.md](./commands.md)
- [flows.md](./flows.md)

## Dependencias internas
- `rules` para configuracoes dinamicas (`SystemConfig`)
- `messaging` para templates
- `integrations` via tools de assistant (indireto)

## Dependencias externas
- SQL Server legado via `pyodbc`
- PostgreSQL (persistencia principal)

## Pontos de atencao para manutencao
- preservacao de idempotencia em imports
- respeito a constraints de dedupe
- cuidado com filtros de data para cargas massivas
- apos cargas LH, stats podem ser recalculados por:
  - rebuild automatico ao final de `import_lh_workday` e `import_lh_pause_events`
  - comando manual `python manage.py rebuild_agent_day_stats --from YYYY-MM-DD --to YYYY-MM-DD --source LH_ALIVE`
