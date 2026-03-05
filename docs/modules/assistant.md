# Modulo Assistant

## Escopo
App de conversacao com IA e automacoes operacionais.

## Models (`apps/assistant/models.py`)
- `AssistantConversation`
  - `created_by`, `created_at`, `title`
- `AssistantMessage`
  - `conversation`, `role` (`user`/`assistant`), `content`, `created_at`
- `AssistantActionLog`
  - `conversation`, `requested_by`, `tool_name`, `tool_args_json`, `status`, `result_text`, `result_json`, `created_at`

## Endpoints (`apps/assistant/urls.py`)
- `POST /assistant/chat`
- `GET /assistant/conversation/<conversation_id>`

## Servicos (`apps/assistant/services`)
- `assistant_service.py`
  - resolve conversa/permissao
  - persiste historico
  - chama OpenAI Responses API
  - executa tool calling (ate 3 chamadas)
  - audita tool execution
- `openai_settings.py`
  - le config via `rules.services.system_config`
- `openai_client.py`
  - cria client OpenAI com timeout
  - valida `OPENAI_API_KEY`
- `tool_registry.py`
  - schemas de tools e dispatch para leitura/acao
- `tools_read.py`
  - consultas operacionais de monitoring
- `tools_actions.py`
  - acoes de notificacao com guardrails

## Permissoes
- Views com `@login_required`.
- Conversa:
  - usuario comum: apenas conversas proprias
  - staff: acesso global
- Action tools: `staff only`.

## Admin
- `AssistantConversationAdmin`
- `AssistantMessageAdmin`
- `AssistantActionLogAdmin`

## Testes
Cobertura em:
- `apps/assistant/tests/test_assistant_endpoints.py`
- `apps/assistant/tests/test_openai_settings.py`
- `apps/assistant/tests/test_tools_read.py`
- `apps/assistant/tests/test_tools_actions.py`
- `apps/assistant/tests/test_assistant_tool_calling.py`
