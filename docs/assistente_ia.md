# Assistente IA

## Objetivo
Fornecer um assistente operacional com:
- UI global (widget flutuante),
- endpoint de chat persistente,
- integracao com OpenAI Responses API,
- tool calling para leitura e acoes controladas,
- auditoria de chamadas de tool.

## Componentes

## Frontend
- `templates/assistant/_assistant_widget.html`
- `static/assistant/assistant_widget.css`
- `static/assistant/assistant_widget.js`

Incluido no shell principal (`templates/layouts/base.html`) via blocks:
- `assistant_widget_assets`
- `assistant_widget`

Desabilitado no admin em `templates/admin/base.html` (blocks vazios).

## Backend
- Rotas:
  - `POST /assistant/chat`
  - `GET /assistant/conversation/<id>`
- View: `apps/assistant/views.py`
- Servico principal: `apps/assistant/services/assistant_service.py`
- Cliente OpenAI: `apps/assistant/services/openai_client.py`
- Config OpenAI: `apps/assistant/services/openai_settings.py`

## Persistencia
- `AssistantConversation`
- `AssistantMessage`
- `AssistantActionLog`

## Fluxo principal
```text
Usuario pergunta
  -> POST /assistant/chat
  -> salva mensagem user
  -> OpenAI Responses API
  -> (opcional) tool calling
  -> salva resposta assistant
  -> retorna conversation_id + answer
```

## Fluxo com tool calling
```text
OpenAI retorna function_call
  -> assistant_service extrai call
  -> tool_registry.execute_tool(...)
  -> grava AssistantActionLog
  -> envia function_call_output para OpenAI
  -> recebe resposta final
```

Limite tecnico: ate 3 tool calls por request (`MAX_TOOL_CALLS_PER_REQUEST`).

## Tools de leitura
- `get_pause_ranking(date, limit=10, pause_type=None)`
- `get_current_pauses(pause_type=None)`
- `get_day_summary(date)`

Implementacao: `apps/assistant/services/tools_read.py`.

## Tools de acao
- `send_message_to_agent(agent_id, template_key, channel, variables)`
- `notify_supervisors(template_key, channel, variables)`

Implementacao: `apps/assistant/services/tools_actions.py`.

## Guardrails de acao
- Staff only: usuario comum recebe `denied`.
- Sem texto livre: acao usa `template_key` + `variables`.
- Allowlist de templates: `ASSISTANT_ALLOWED_TEMPLATES_JSON`.
- Throttle anti-spam: `NOTIFY_THROTTLE_MINUTES`.
- Auditoria sempre: `AssistantActionLog`.
- Rastreio de envio: `NotificationHistory`.

## Prompt de sistema
Configurado em `assistant_service.py` com orientacoes para:
- responder objetivamente,
- pedir contexto quando faltar dado,
- usar tools de acao (nao texto livre),
- pedir confirmacao para acao sensivel.

## Configuracao OpenAI
Defaults (quando nao ha `SystemConfig`):
- enabled: `true`
- model: `gpt-4.1-mini`
- temperature: `0.2`
- max_output_tokens: `600`
- timeout_seconds: `30`

API key: `OPENAI_API_KEY` (somente env).

## Comportamento de erro
- `OPENAI_ENABLED=false`: resposta fixa "Assistente desativado nas configuracoes."
- Sem API key: resposta amigavel de configuracao (200 no endpoint).
- Falha de rede/OpenAI: resposta amigavel temporaria (200 no endpoint).
