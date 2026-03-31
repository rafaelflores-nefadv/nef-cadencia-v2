# Integracoes Externas

## 1) SQL Server legado (LH_ALIVE)
Finalidade:
- Fonte de eventos e jornadas operacionais.

Tecnologia:
- ODBC + `pyodbc`.

Uso no sistema:
- `sync_legacy_events` (tabela legado parametrizavel)
- `import_lh_workday` (view `VW_LH_AGENT_WORKDAY`)
- `import_lh_pause_events` (view `VW_LH_AGENT_PAUSE_EVENTS`)
- `check_legacy_connection` (teste de conectividade)

Fluxo:
```text
SQL Server -> commands monitoring -> PostgreSQL
```

## 2) OpenAI Responses API
Finalidade:
- Responder perguntas operacionais e acionar tools.

Componentes:
- `assistant_service.run_chat`
- `openai_client.get_openai_client`
- `tool_registry.execute_tool`

Controles:
- habilitacao e parametros via `SystemConfig` (`OPENAI_*`)
- auditoria de tool calls em `AssistantActionLog`

## 3) Canais de notificacao
Modelo:
- Templates em `messaging.MessageTemplate`
- Conectores em `integrations.Integration`
- Historico em `monitoring.NotificationHistory`

Canais previstos em `ChannelChoices`:
- `chatseguro`
- `email`
- `webhook`
- `slack`
- `teams`

Estado atual no codigo:
- `chatseguro`: envio interno stub (sucesso simulado)
- `email`: envio real via `send_mail`
- `webhook`: POST HTTP via `urllib`
- `slack`/`teams`: retorno `not implemented` no dispatcher atual

## 4) WAHA (WhatsApp API)
Nao ha cliente WAHA dedicado no codigo atual.

Como acoplar WAHA sem mudar arquitetura:
- criar `Integration` para canal de saida (tipicamente `webhook` ou canal dedicado futuro)
- apontar `config_json.url` para endpoint WAHA
- manter trilha em `NotificationHistory`

## 5) Boas praticas de integracao
- nao armazenar segredos em codigo
- validar timeout e retry por integracao
- monitorar falhas por `NotificationHistory.status=ERROR`
- usar `check_legacy_connection` antes de janelas massivas de import
