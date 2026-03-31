# Modulo Monitoring

## Objetivo
O app `monitoring` concentra ingestao operacional, agregacao diaria e BI operacional da plataforma.

Responsabilidades principais:
- ingestao de dados do LH (pausas e jornada)
- consolidacao diaria por agente (`AgentDayStats`)
- dashboard operacional (cards, rankings, alertas)
- classificacao de pausas e impacto em metricas/risco
- historico de execucoes de jobs (`JobRun`)

## Pipeline de dados (fonte -> dashboard)
```text
LH (fonte externa SQL Server)
   |
   |  import_lh_pause_events / import_lh_workday / import_lh_all / import_lh_alive
   |  sync_legacy_events
   v
AgentEvent + AgentWorkday   (tabelas brutas de ingestao)
   |
   |  rebuild_agent_day_stats
   v
AgentDayStats               (agregacao diaria)
   |
   v
Dashboard operacional       (/dashboard)
```

### Tabelas brutas x agregadas
- Brutas (ingestao LH): `AgentEvent`, `AgentWorkday`
- Agregada: `AgentDayStats`

### Rebuild de stats
Comando oficial:
- `python manage.py rebuild_agent_day_stats --date YYYY-MM-DD`
- `python manage.py rebuild_agent_day_stats --from YYYY-MM-DD --to YYYY-MM-DD`
- opcional: `--source LH_ALIVE`

## Protecao de tabelas brutas do monitoring
`AgentEvent` e `AgentWorkday` sao protegidas por padrao.

Regras:
- escrita/delecao via ORM fora dos fluxos oficiais e bloqueada
- `PermissionDenied` e levantado em contexto nao autorizado
- admin e readonly para essas tabelas

Comandos autorizados para mutacao bruta:
- `import_lh_pause_events`
- `import_lh_workday`
- `import_lh_all`
- `import_lh_alive`
- `sync_legacy_events`
- `wipe_lh_import`

Nao usar:
- `manage.py shell` para inserir/alterar/apagar dados brutos
- fixtures/scripts arbitrarios em `AgentEvent`/`AgentWorkday`

## Classificacao de pausas
### Categorias internas (backend)
- `LEGAL`
- `NEUTRAL`
- `HARMFUL`
- `UNCLASSIFIED` (fallback interno quando nao ha classificacao ativa)

### Nomenclatura operacional (frontend)
- `Tempo Produtivo`
- `Tempo Neutro`
- `Tempo Improdutivo`
- `Tempo Nao Classificado`

### Onde configurar
- Admin global -> Monitoring -> Classificacao de pausas
- Rota: `/admin/monitoring/pause-classification`

### Como classificar
- adicionar pausa em uma categoria
- remover classificacao (seta `is_active=False`)
- mover pausa entre categorias

### Impacto da classificacao
A classificacao impacta diretamente:
- `tempo_produtivo`
- `tempo_neutro`
- `tempo_improdutivo`
- `tempo_nao_classificado`
- taxa de ocupacao (`tempo_produtivo / tempo_logado`)
- risk scoring
- rankings e alertas da dashboard

## Dashboard operacional
### Cards principais
- Agentes com atividade
- Eventos
- Tempo Logado
- Tempo Produtivo
- Tempo Neutro
- Tempo Improdutivo
- Tempo Nao Classificado
- Taxa de ocupacao

### Rankings
- Top 10 por tempo improdutivo
- Top 10 por quantidade de pausas improdutivas
- Top 10 agentes mais produtivos
- Agentes com maior risco

### Origem dos dados
- base principal: agregacoes de `AgentEvent` + `AgentWorkday`
- suporte complementar: `AgentDayStats` (com fallback controlado quando necessario)

### Filtros temporais suportados
Campos suportados na rota `/dashboard`:
- `year` (ano)
- `month` (mes de 1 a 12)
- `date_from` e `date_to` (periodo personalizado)
- `quick_range` (`today`, `yesterday`, `last_7_days`, `this_month`, `last_month`, `this_year`)
- `data_ref` (compatibilidade com filtro legado de dia unico)

Prioridade de resolucao do periodo:
1. `quick_range` valido
2. `date_from` + `date_to` validos (se `date_from > date_to`, o intervalo nao e aplicado e a UI mostra aviso)
3. `year` + `month` (mes inteiro)
4. apenas `year` (ano inteiro)
5. apenas `month` sem `year` nao aplica filtro e gera aviso explicito
6. `data_ref` (compatibilidade)
7. sem filtros: dia atual (`timezone.localdate()`)

Comportamento padrao:
- sem querystring, o dashboard continua abrindo no dia atual (comportamento legado)
- todos os indicadores, rankings, graficos e alertas usam o mesmo intervalo resolvido no backend
- os filtros permanecem na URL para refresh e compartilhamento

Nota de performance:
- filtros usam campos indexados para consulta temporal:
  - `AgentEvent.dt_inicio` (`>= inicio` e `< fim`)
  - `AgentWorkday.work_date` (`>=` e `<=`)
  - `AgentDayStats.data_ref` (`>=` e `<=`)
- nao houve mudanca estrutural de schema/migration para habilitar os novos filtros

### Regras de calculo (resumo)
- `tempo_produtivo`: pausas classificadas como `LEGAL` (com fallback operacional quando aplicavel)
- `tempo_neutro`: pausas `NEUTRAL`
- `tempo_improdutivo`: pausas `HARMFUL`
- `tempo_nao_classificado`: pausas sem classificacao ativa
- `ocupacao`: `tempo_produtivo / tempo_logado`

## Risk scoring
Arquivo principal:
- `apps/monitoring/services/risk_scoring.py`

Fatores de risco:
- tempo improdutivo
- quantidade de pausas improdutivas
- baixa ocupacao
- tempo nao classificado
- agente sem atividade

Principio importante:
- tempo produtivo (`LEGAL`) nao penaliza diretamente o score

Alertas operacionais usam severidade:
- `crit`
- `warn`
- `info`

## Procedimento de recuperacao do monitoring
Usar quando houver inconsistencia de dados, buraco de importacao ou dashboard incoerente.

1. Reimportar dados LH do periodo
- `python manage.py import_lh_workday --date YYYY-MM-DD`
- `python manage.py import_lh_pause_events --date YYYY-MM-DD`
- para intervalo: `python manage.py import_lh_workday --from YYYY-MM-DD --to YYYY-MM-DD`
- para intervalo: `python manage.py import_lh_pause_events --from YYYY-MM-DD --to YYYY-MM-DD`
- opcional: `python manage.py import_lh_all --date YYYY-MM-DD`

2. Rebuild de `AgentDayStats`
- dia unico: `python manage.py rebuild_agent_day_stats --date YYYY-MM-DD --source LH_ALIVE`
- intervalo: `python manage.py rebuild_agent_day_stats --from YYYY-MM-DD --to YYYY-MM-DD --source LH_ALIVE`

3. Validar contagens
- verificar `AgentEvent` e `AgentWorkday` para o periodo
- verificar `AgentDayStats` para o mesmo periodo

4. Validar dashboard
- dia unico: `/dashboard?data_ref=YYYY-MM-DD`
- por ano/mes: `/dashboard?year=YYYY&month=MM`
- periodo customizado: `/dashboard?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
- conferir cards, rankings, risco e alertas

## Referencias do modulo
- [models.md](./models.md)
- [services.md](./services.md)
- [commands.md](./commands.md)
- [flows.md](./flows.md)
