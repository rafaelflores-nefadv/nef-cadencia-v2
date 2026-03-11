# NEF Cadencia v2 - Documentacao Tecnica

## Objetivo da plataforma
O projeto `nef-cadencia-v2` e uma plataforma Django para monitoramento operacional de agentes, ingestao de dados do legado LH, aplicacao de regras e notificacoes assistidas por IA.

## Estado atual (resumo)
A documentacao reflete o estado atual apos evolucoes do `monitoring`:
- classificacao de pausas por categoria operacional
- dashboard com foco em BI operacional e filtro temporal por ano/mes/periodo
- risk scoring centralizado
- blindagem de tabelas brutas de ingestao
- pipeline LH -> bruto -> agregado -> dashboard
- comandos de importacao/rebuild/recuperacao

## Leitura recomendada
1. [ARCHITECTURE.md](./ARCHITECTURE.md)
2. [DATABASE.md](./DATABASE.md)
3. [MANAGEMENT_COMMANDS.md](./MANAGEMENT_COMMANDS.md)
4. [modules/monitoring/README.md](./modules/monitoring/README.md)
5. [modules/monitoring/services.md](./modules/monitoring/services.md)

## Mapa da documentacao
### Visao geral
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [DATABASE.md](./DATABASE.md)
- [DEPLOYMENT.md](./DEPLOYMENT.md)
- [MANAGEMENT_COMMANDS.md](./MANAGEMENT_COMMANDS.md)
- [INTEGRATIONS.md](./INTEGRATIONS.md)

### Por modulo
- [modules/monitoring/README.md](./modules/monitoring/README.md)
- [modules/messaging/README.md](./modules/messaging/README.md)
- [modules/rules/README.md](./modules/rules/README.md)
- [modules/integrations/README.md](./modules/integrations/README.md)

## Apps Django e responsabilidades
- `accounts`: autenticacao e contexto de menu
- `monitoring`: ingestao LH, stats diarios, dashboard operacional, risco, alertas
- `rules`: configuracao dinamica (`SystemConfig`)
- `messaging`: templates de mensagens
- `integrations`: configuracoes de conectores
- `assistant`: API de chat e tools
- `reports`: app reservado

## Stack tecnica
- Backend: Django 4.2.x
- Banco principal: PostgreSQL
- Legado: SQL Server via `pyodbc`
- IA: OpenAI Responses API
- Frontend: templates Django + Tailwind

## Convencoes operacionais
- dados importados do LH usam `source="LH_ALIVE"`
- tabelas brutas: `AgentEvent` e `AgentWorkday`
- tabela agregada diaria: `AgentDayStats`
- mutacao de bruto so em comandos oficiais de ingestao/sync/wipe
