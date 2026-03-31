# Monitoring - Fluxos

## 1) Ingestao LH por views oficiais
```text
VW_LH_AGENT_WORKDAY ------------> import_lh_workday -------> AgentWorkday
VW_LH_AGENT_PAUSE_EVENTS -------> import_lh_pause_events ---> AgentEvent
```

## 2) Ingestao incremental legado (tabela)
```text
LEGACY_EVENTS_TABLE --> sync_legacy_events --> LegacySyncService --> Agent/AgentEvent
```

## 3) Rebuild de agregacao diaria
```text
AgentEvent + AgentWorkday
        |
        v
rebuild_agent_day_stats
        |
        v
AgentDayStats
```

## 4) Classificacao de pausas
```text
AgentEvent.nm_pausa
        |
        v
PauseClassification + resolve_pause_category
        |
        v
Tempo Produtivo / Neutro / Improdutivo / Nao Classificado
```

## 5) Dashboard operacional
```text
querystring filtros (year/month/date_from/date_to/quick_range/data_ref)
        |
        v
dashboard_period_filter.resolve_dashboard_period_filter
        |
        v
intervalo temporal unico (inicio/fim + metadados de filtro)
        |
        v
AgentEvent + AgentWorkday + AgentDayStats + JobRun
        |
        v
DashboardView
        |
        v
cards + rankings + risco + alertas
```

## 6) Blindagem de bruto
```text
ORM write em AgentEvent/AgentWorkday
        |
        +--> comando oficial autorizado? ------ sim --> permite
        |
        +--> nao -------------------------------> PermissionDenied
```

## 7) Recuperacao operacional
```text
1. import_lh_* (reimportar periodo)
2. rebuild_agent_day_stats
3. validar contagens em bruto/agregado
4. validar dashboard para data/mes/ano/periodo
```
