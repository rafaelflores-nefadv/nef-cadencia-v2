# Monitoring - Models

## Visao geral
Modelos do modulo `monitoring` separam dados brutos de ingestao, dados agregados e auditoria operacional.

## Modelos de ingestao (dados brutos)
### `AgentEvent`
Eventos operacionais (logon/logoff/pausa) importados do LH.

Campos chave:
- `source`, `source_event_hash`, `ext_event`
- `agent`, `cd_operador`, `tp_evento`, `nm_pausa`
- `dt_inicio`, `dt_fim`, `duracao_seg`
- `dt_captura_origem`, `raw_payload`

Constraints:
- unico `(source, source_event_hash)`
- unico parcial `(source, ext_event)` quando preenchido
- `duracao_seg >= 0` (quando nao nulo)

### `AgentWorkday`
Jornada diaria do agente importada do LH.

Campos chave:
- `source`, `ext_event`, `cd_operador`, `nm_operador`
- `work_date`, `dt_inicio`, `dt_fim`, `duracao_seg`
- `dt_captura_origem`, `raw_payload`

Constraints:
- unico `(source, cd_operador, work_date)`
- unico `(source, ext_event)`

## Modelo de agregacao
### `AgentDayStats`
Agregado diario por agente para suportar BI e ranking.

Campos chave:
- `agent`, `cd_operador`, `data_ref`
- `qtd_pausas`, `tempo_pausas_seg`
- `ultimo_logon`, `ultimo_logoff`, `ultima_pausa_inicio`, `ultima_pausa_fim`

## Modelo de classificacao de pausas
### `PauseClassification`
Mapeia nomes de pausa para categorias operacionais.

Campos chave:
- `source` (vazio = global)
- `pause_name`, `pause_name_normalized`
- `category` (`LEGAL`, `NEUTRAL`, `HARMFUL`)
- `is_active`

Constraint funcional:
- uma pausa ativa nao pode existir em mais de uma categoria para o mesmo `source`

## Modelos de suporte operacional
- `Agent`: cadastro normalizado de operador
- `NotificationHistory`: historico de notificacoes
- `NotificationThrottle`: limite de envio
- `JobRun`: historico de execucao de jobs

## Relacoes principais
```text
Agent 1---N AgentEvent
Agent 1---N AgentDayStats
Agent 1---N NotificationHistory (opcional)
Agent 1---N NotificationThrottle

AgentWorkday (chave logica por operador/data)
JobRun (independente)
PauseClassification (catalogo tecnico)
```

## Nota de seguranca
`AgentEvent` e `AgentWorkday` sao modelos de ingestao LH com protecao de escrita no ORM.
Nao usar esses modelos para dados de teste manual em banco operacional.
