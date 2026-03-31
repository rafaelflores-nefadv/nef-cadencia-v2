# Modulo Monitoring (indice rapido)

Este arquivo e um indice resumido.
Documentacao detalhada e atualizada do modulo esta em:
- [modules/monitoring/README.md](./monitoring/README.md)
- [modules/monitoring/models.md](./monitoring/models.md)
- [modules/monitoring/services.md](./monitoring/services.md)
- [modules/monitoring/commands.md](./monitoring/commands.md)
- [modules/monitoring/flows.md](./monitoring/flows.md)

## Resumo do estado atual
- pipeline LH -> bruto (`AgentEvent`/`AgentWorkday`) -> `AgentDayStats` -> dashboard
- classificacao de pausas integrada em metricas, rankings, risco e alertas
- UI administrativa de classificacao em `/admin/monitoring/pause-classification`
- tabelas brutas com blindagem de escrita no ORM
