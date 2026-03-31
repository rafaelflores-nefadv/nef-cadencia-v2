# Monitoring - Services

## Visao geral
Servicos do `monitoring` organizam ingestao, classificacao, agregacao e risco operacional.

## `lh_import_utils.py`
Utilitarios comuns para comandos de importacao LH.

Principais responsabilidades:
- parsing de argumentos de data (`--today`, `--date`, `--from/--to`, `--days`, `--all`)
- resolucao de janela temporal
- conexao SQL Server (`pyodbc`) via env vars `LEGACY_*`
- normalizacao de tipos (`to_date`, `to_aware_datetime`, `to_bigint`, etc.)

## `day_stats_service.py`
Consolidacao diaria para `AgentDayStats`.

Funcoes:
- `rebuild_agent_day_stats(date_from, date_to, source=None)`
- `infer_rebuild_window_for_all(source=None)`

Comportamento:
- agrega `AgentEvent` por agente/dia
- inclui pares de `AgentWorkday` para nao perder atividade sem pausa
- cria/atualiza `AgentDayStats` com idempotencia

## `dashboard_period_filter.py`
Resolucao central do filtro temporal do dashboard.

Responsabilidades:
- interpretar querystring da dashboard (`year`, `month`, `date_from`, `date_to`, `quick_range`, `data_ref`)
- aplicar prioridade de regras para chegar a um unico intervalo
- validar inconsistencias de entrada (ex.: `date_from > date_to`, `month` sem `year`)
- expor janela temporal indexavel para queries (`dt_start`, `dt_end`, `date_from`, `date_to`)
- montar utilitarios de exibicao/comando (`period_label`, argumentos `--date` ou `--from/--to`)

Atalhos rapidos suportados:
- `today`
- `yesterday`
- `last_7_days`
- `this_month`
- `last_month`
- `this_year`

## `pause_classification.py`
Camada de classificacao de pausas.

Categorias internas:
- `LEGAL`, `NEUTRAL`, `HARMFUL`, `UNCLASSIFIED`

Funcoes:
- `resolve_pause_category(pause_name, source=None)`
- `list_distinct_event_pause_names(source=None)`
- `list_event_pause_names_by_classification(source=None)`

Uso principal:
- alimentar dashboard por categoria operacional
- abastecer UI administrativa de classificacao

## `risk_scoring.py`
Formula central do risco por agente.

Configuracao (via `RiskScoringConfig`):
- thresholds de ocupacao
- limites de tempo/qtd improdutiva
- limite de percentual nao classificado
- pesos de penalizacao

Funcoes:
- `calculate_agent_risk(metric, config=...)`
- `calculate_no_activity_risk(config=...)`
- `is_no_activity_metric(metric)`

Regras de negocio:
- produtivo (`LEGAL`) nao penaliza diretamente
- neutro penaliza pouco
- improdutivo penaliza forte
- nao classificado gera atencao
- sem atividade gera score alto

## `legacy_sync_service.py`
Sincronizacao incremental da tabela legado (nao via views LH).

Fluxo:
- busca eventos por janela movel
- normaliza payload
- upsert `Agent`
- upsert `AgentEvent`
- rebuild de `AgentDayStats` para pares afetados

## `guards.py`
Blindagem das tabelas brutas (`AgentEvent` e `AgentWorkday`).

Regra:
- mutacoes ORM (`create/save/delete/get_or_create/update_or_create/bulk_*`) sao bloqueadas por padrao
- apenas comandos oficiais de ingestao/sync/wipe podem mutar
- fora desses fluxos, ocorre `PermissionDenied`

Objetivo:
- impedir contaminacao de dado bruto por shell/admin/scripts manuais

## `utils.py`
Utilitarios de tempo e formatacao.

Funcoes relevantes:
- `hms_to_seconds`
- `format_seconds_hhmmss`
- aliases de compatibilidade (`format_seconds_hhmm`)

Padrao visual da dashboard:
- `hh:mm:ss`
