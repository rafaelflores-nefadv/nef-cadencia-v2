# API Interna - Assistant

Base path: `/assistant`

## Autenticacao
Ambos os endpoints exigem usuario autenticado (`@login_required`).

## GET `/assistant/`

Pagina dedicada do Eustacio.

Comportamentos relevantes:
- renderiza o layout persistido do assistente
- lista apenas conversas do usuario logado
- carrega opcionalmente a conversa selecionada via `?conversation_id=<id>`
- exibe contador e limite de conversas salvas no frontend
- nao reaproveita a sessao temporaria do widget

## GET/POST `/assistant/conversations`

API da pagina dedicada para listar ou criar conversas persistidas do usuario logado.

### `GET` response (200)
```json
{
  "conversations": [
    {
      "id": 12,
      "title": "Resumo operacional de hoje",
      "origin": "page",
      "status": "active",
      "is_persistent": true,
      "created_at": "2026-03-09T20:00:00+00:00",
      "updated_at": "2026-03-09T20:05:00+00:00",
      "message_count": 4
    }
  ],
  "conversation_count": 1,
  "conversation_limit": 100
}
```

### `POST` response (201)
```json
{
  "conversation": {
    "id": 13,
    "title": "Nova conversa",
    "origin": "page",
    "status": "active",
    "is_persistent": true,
    "created_at": "2026-03-09T20:10:00+00:00",
    "updated_at": "2026-03-09T20:10:00+00:00",
    "message_count": 0
  },
  "conversation_count": 2,
  "conversation_limit": 100
}
```

Comportamentos relevantes:
- lista apenas historico do usuario logado
- cria conversa persistida com `origin=page`
- respeita o limite de conversas do usuario
- se o limite for atingido, retorna `409`
- registra auditoria com `event_type=page_conversation_created`

## GET `/assistant/conversations/<conversation_id>`

Retorna a conversa persistida da pagina dedicada.

### Response (200)
```json
{
  "conversation": {
    "id": 12,
    "title": "Resumo operacional de hoje",
    "origin": "page",
    "status": "active",
    "is_persistent": true,
    "created_at": "2026-03-09T20:00:00+00:00",
    "updated_at": "2026-03-09T20:05:00+00:00",
    "message_count": 4,
    "messages": [
      {
        "role": "user",
        "content": "Pergunta",
        "created_at": "2026-03-09T20:00:10+00:00"
      }
    ]
  }
}
```

## POST `/assistant/conversations/<conversation_id>/delete`

Exclui logicamente uma conversa persistida da pagina dedicada.

### Response (200)
```json
{
  "deleted": true,
  "conversation_id": 12,
  "conversation_count": 1,
  "conversation_limit": 100
}
```

## POST `/assistant/chat`

Endpoint persistente do modulo. Mantido para fluxos que salvam historico diretamente.

## Request body
```json
{
  "text": "Quem esta em pausa agora?",
  "conversation_id": 12,
  "origin": "widget"
}
```

Campos:
- `text` (string, obrigatorio)
- `conversation_id` (int, opcional)
- `origin` (`widget` ou `page`, opcional, default `widget`)

## Response (200)
```json
{
  "conversation_id": 12,
  "answer": "...",
  "conversation": {
    "id": 12,
    "messages": []
  },
  "processing_status": "completed",
  "processing_statuses": [
    {"status": "understanding_query", "label": "Entendendo sua pergunta"},
    {"status": "checking_context", "label": "Verificando o contexto da conversa"}
  ]
}
```

Comportamentos relevantes:
- cria nova conversa quando `conversation_id` invalido/sem permissao.
- a nova conversa nasce persistida por usuario, com titulo automatico e `origin` da requisicao.
- persiste mensagem do usuario e do assistente.
- quando a conversa existe, retorna a thread atualizada em `conversation`, incluindo o historico de mensagens.
- registra auditoria consolidada em `AssistantAuditLog`.
- aplica resolucao semantica operacional antes do guardrail e da capability final.
- quando a linguagem do negocio exige esclarecimento ou depende de regra operacional nao cadastrada, responde no backend sem chamar o modelo.
- aplica validacao de escopo antes do OpenAI.
- quando a mensagem estiver fora do escopo, retorna a recusa padrao do Eustacio sem consultar o modelo.
- aplica validacao de capacidade real antes do OpenAI.
- quando a funcionalidade nao existir no ambiente atual, retorna resposta transparente de nao suportado.
- aplica pos-validacao de saida antes de responder ao usuario.
- quando a resposta do modelo sair do dominio da plataforma, substitui pela resposta segura padrao.
- quando a resposta aparentar consulta, dado ou acao nao verificada, substitui por resposta transparente de nao confirmacao.
- quando a tool nao retorna dados suficientes, responde explicitamente que nao encontrou dados suficientes.
- quando a tool falha, responde explicitamente que nao foi possivel concluir a consulta/acao naquele momento.
- quando `OPENAI_ENABLED=false`, responde mensagem de assistente desativado.
- quando falta `OPENAI_API_KEY`, responde texto amigavel de configuracao.
- quando o usuario atinge o limite de conversas persistidas, retorna resposta clara e `conversation_id: null`.
- toda resposta persistida ou bloqueada gera `AssistantAuditLog(event_type=chat_message)`.
- o payload inclui `processing_status` e `processing_statuses` para suportar UX de etapas intermediarias.
- esses campos descrevem apenas a requisicao corrente; o frontend nao deve reaproveita-los para restaurar um estado visual de processamento em refresh, reopen ou troca de conversa.

## POST `/assistant/widget/chat`

Endpoint temporario do widget flutuante.

## Request body
```json
{
  "text": "Quem esta em pausa agora?",
  "widget_session_id": "widget_abc123xyz"
}
```

Campos:
- `text` (string, obrigatorio)
- `widget_session_id` (string, obrigatorio)

## Response (200)
```json
{
  "answer": "...",
  "conversation_id": null,
  "widget_session_id": "widget_abc123xyz",
  "messages": [
    {"role": "user", "content": "Pergunta"}
  ],
  "saved_conversation_id": null,
  "already_saved": false,
  "processing_status": "completed",
  "processing_statuses": [
    {"status": "understanding_query", "label": "Entendendo sua pergunta"}
  ]
}
```

Comportamentos relevantes:
- nao cria `AssistantConversation` automaticamente
- nao grava `AssistantMessage` automaticamente
- usa a sessao temporaria do widget para contexto entre mensagens
- `widget_session_id` e a fonte da verdade da thread temporaria
- o endpoint devolve `messages` com a thread temporaria atualizada
- continua registrando `AssistantAuditLog`
- pode registrar `AssistantActionLog` mesmo sem conversa persistida
- audita essas interacoes com `event_type=chat_message` e `origin=widget`
- o widget deve limpar qualquer status visual assim que a request terminar ou a sessao temporaria for encerrada

## POST `/assistant/widget/session/end`

Encerra explicitamente a sessao temporaria atual do widget.

## Request body
```json
{
  "widget_session_id": "widget_abc123xyz"
}
```

## Response (200)
```json
{
  "ended": true
}
```

Comportamentos relevantes:
- gera auditoria com `event_type=widget_session_ended`
- pode existir auditoria sem conversa persistida associada

## POST `/assistant/widget/session/save`

Salva a sessao temporaria atual como conversa persistida.

## Request body
```json
{
  "widget_session_id": "widget_abc123xyz"
}
```

## Response (200)
```json
{
  "conversation_id": 12,
  "already_saved": false,
  "title": "Quais agentes estao em pausa agora?"
}
```

Comportamentos relevantes:
- cria a conversa persistida com `origin=widget`
- persiste o snapshot atual da sessao temporaria
- usa titulo automatico da primeira mensagem util
- evita duplicacao quando a mesma sessao ja foi salva
- se nao houver mensagens para salvar, retorna `400`
- se o limite de conversas persistidas for atingido, retorna `409`
- gera auditoria com `event_type=widget_session_saved`

## Possiveis erros de validacao
- `400` JSON invalido:
```json
{"detail":"Invalid JSON body."}
```
- `400` sem `text`:
```json
{"detail":"Field 'text' is required."}
```

## GET `/assistant/conversation/<conversation_id>`

## Response (200)
```json
{
  "conversation_id": 12,
  "messages": [
    {
      "role": "user",
      "content": "Pergunta",
      "created_at": "2026-03-05T10:10:10.000000+00:00"
    },
    {
      "role": "assistant",
      "content": "Resposta",
      "created_at": "2026-03-05T10:10:11.000000+00:00"
    }
  ]
}
```

Permissao:
- usuario comum acessa apenas conversas criadas por ele.
- staff pode acessar qualquer conversa.
- conversas marcadas como `deleted` nao sao retornadas.
- sem permissao -> `404`.

## Observabilidade

Eventos auditados:
- `chat_message`
- `page_conversation_created`
- `widget_session_saved`
- `widget_session_ended`
- `conversation_deleted`

Status finais padronizados:
- `completed`
- `blocked_scope`
- `blocked_capability`
- `blocked_limit`
- `no_data`
- `disabled`
- `config_error`
- `tool_failure`
- `temporary_failure`
- `fail_safe`

Resultados padronizados de tools:
- `success`
- `error`
- `denied`

Payload semantico auditado:
- `semantic_resolution_json.original_text`
- `semantic_resolution_json.normalized_text`
- `semantic_resolution_json.intent`
- `semantic_resolution_json.business_rule`
- `semantic_resolution_json.metric`
- `semantic_resolution_json.subject`
- `semantic_resolution_json.ranking_order`
- `semantic_resolution_json.limit`
- `semantic_resolution_json.reused_context`
- `semantic_resolution_json.context_applied_fields`
- `semantic_resolution_json.needs_clarification`
- `semantic_resolution_json.needs_business_definition`
- `semantic_resolution_json.reason`

Servico interno de metricas:
- `apps/assistant/services/metrics_service.py`
- funcao principal: `get_assistant_metrics(user=None)`

Metricas disponiveis:
- `messages_total`
- `saved_conversations_total`
- `interactions_by_origin`
- `events_by_type`
- `blocked_scope_total`
- `blocked_capability_total`
- `tool_failures_total`
- `fallbacks_total`
- `successful_responses_total`
