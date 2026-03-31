# Modulo Assistant

## Escopo
App de conversacao com IA e automacoes operacionais restrito ao contexto do sistema e das capacidades reais do assistente.

## Models (`apps/assistant/models.py`)
- `AssistantConversation`
  - `created_by`, `origin`, `status`, `is_persistent`, `created_at`, `updated_at`, `title`
- `AssistantMessage`
  - `conversation`, `role` (`user`/`assistant`/`system`), `content`, `created_at`
- `AssistantAuditLog`
  - `conversation`, `user`, `origin`, `event_type`, `input_text`, `scope_classification`, `capability_classification`, `capability_id`, `tools_attempted_json`, `tools_succeeded_json`, `block_reason`, `fallback_reason`, `final_response_status`, `response_text`, `semantic_resolution_json`, `created_at`
- `AssistantUserPreference`
  - `user`, `max_saved_conversations`, `created_at`, `updated_at`
- `AssistantActionLog`
  - `conversation`, `requested_by`, `tool_name`, `tool_args_json`, `status`, `result_text`, `result_json`, `created_at`

## Endpoints (`apps/assistant/urls.py`)
- `GET /assistant/`
- `POST /assistant/chat`
- `GET/POST /assistant/conversations`
- `GET /assistant/conversations/<conversation_id>`
- `POST /assistant/conversations/<conversation_id>/delete`
- `POST /assistant/widget/chat`
- `POST /assistant/widget/session/end`
- `POST /assistant/widget/session/save`
- `GET /assistant/conversation/<conversation_id>`

## Servicos (`apps/assistant/services`)
- `assistant_service.py`
  - resolve conversa/permissao
  - persiste historico quando o fluxo e persistido
  - aplica validacao de entrada, capacidade, pos-validacao e fail-safe
  - executa tool calling controlado
  - registra auditoria consolidada do chat
- `assistant_config.py`
  - centraliza identidade do Eustacio, respostas fixas e sinais de dominio
- `business_glossary.py`
  - centraliza sinonimos, jargoes e expressoes operacionais do negocio
- `semantic_resolution.py`
  - normaliza linguagem humana para intencoes seguras
  - resolve polaridade, metrica, sujeito, limite, periodo e regra de negocio
  - reutiliza contexto recente da conversa quando apropriado
- `processing_status.py`
  - centraliza os estados intermediarios de processamento
  - mapeia estados internos para mensagens amigaveis de UI
  - define sequencias fallback para widget e pagina dedicada
- `conversation_store.py`
  - cria conversa persistida
  - adiciona mensagem
  - lista conversas do usuario
  - exclui conversa por soft delete
  - valida limite de conversas salvas
  - gera titulo automatico
- `audit_service.py`
  - registra auditoria consolidada por evento
- `metrics_service.py`
  - consolida metricas operacionais por usuario ou globalmente
- `widget_session_service.py`
  - controla a sessao temporaria do widget
  - salva a sessao temporaria sob demanda
- `views.py`
  - renderiza a pagina dedicada
  - expoe a API da pagina e do widget
  - registra auditoria segura para criacao/exclusao de conversa e eventos do widget
- `capabilities.py`
  - matriz central de capacidades suportadas
  - valida veracidade operacional da resposta com base nas tools executadas
- `guardrails.py`
  - classifica entrada e saida como `DENTRO_DO_ESCOPO` ou `FORA_DO_ESCOPO`
- `system_prompt.py`
  - reforca a persona fixa e as restricoes do modelo
- `observability.py`
  - centraliza origem, `event_type`, status finais, motivos de bloqueio/fallback e resultados de tool

## Permissoes
- Views com `@login_required`
- usuario comum acessa apenas conversas proprias
- staff pode acessar qualquer conversa
- novas conversas persistidas respeitam o limite configurado por usuario
- exclusao de conversa usa `status=deleted`, sem apagar auditoria
- action tools sao `staff only`

## Titulos de conversa
- a primeira mensagem util do usuario define o titulo
- entradas genericas como `oi`, `ola` e `teste` sao ignoradas
- fallback: `Nova conversa`
- o tamanho do titulo e limitado automaticamente

## Auditoria
- `AssistantAuditLog` registra escopo, capacidade, tools tentadas, tools bem-sucedidas, motivos, status final e tipo de evento
- `semantic_resolution_json` registra expressao original, forma normalizada, regra de negocio usada, reaproveitamento de contexto e necessidade de esclarecimento
- `AssistantActionLog` registra cada tool individualmente com resultado padronizado
- a auditoria do widget temporario continua existindo mesmo sem `AssistantConversation`

## Status de processamento
Servico: `apps/assistant/services/processing_status.py`

Estados padronizados:
- `understanding_query`
- `checking_context`
- `resolving_intent`
- `querying_database`
- `running_tool`
- `filtering_results`
- `building_response`
- `validating_response`
- `completed`
- `failed`

Publicacao:
- `assistant_service.run_chat()` retorna `processing_statuses` e `processing_status`
- o widget e a pagina dedicada exibem um indicador leve com esses estados
- quando o backend nao consegue granularidade completa durante a requisicao, o frontend usa uma sequencia fallback por heuristica
- a fonte da verdade do status e a requisicao ativa atual no frontend, nao o historico da conversa
- `processing_statuses` nao deve ser persistido como estado visual nem restaurado apos refresh, reopen ou troca de conversa
- fechar o widget ou trocar de conversa invalida imediatamente qualquer request visual anterior e limpa timers de animacao

Eventos relevantes auditados:
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

Resultados padronizados de tool:
- `success`
- `error`
- `denied`

## Metricas
Servico: `apps/assistant/services/metrics_service.py`

`get_assistant_metrics(user=...)` retorna:
- `messages_total`
- `saved_conversations_total`
- `interactions_by_origin`
- `events_by_type`
- `blocked_scope_total`
- `blocked_capability_total`
- `tool_failures_total`
- `fallbacks_total`
- `successful_responses_total`

Regras:
- `blocked_*`, `fallbacks_total` e `successful_responses_total` consideram apenas eventos `chat_message`
- `tool_failures_total` usa `AssistantActionLog(status="error")`
- `interactions_by_origin` e `events_by_type` consideram todos os eventos auditados

## Widget flutuante
- usa sessao temporaria, nao historico persistido automatico
- `widget_session_id` e o identificador da thread temporaria
- fechar no `X`, `Esc`, clique fora ou alternar o FAB apenas oculta o drawer
- a conversa temporaria continua viva enquanto a pagina atual estiver aberta
- refresh da pagina recria a sessao do zero
- `Salvar conversa` persiste apenas o snapshot atual da sessao
- auditoria continua ativa mesmo sem conversa persistida

## Pagina dedicada
- rota principal: `/assistant/`
- integrada ao template principal do sistema e ao menu lateral
- lista historico persistido apenas do usuario logado
- `conversation_id` e a fonte da verdade da thread persistida
- permite criar, abrir, alternar e excluir conversas
- envia mensagens usando o mesmo `assistant_service.py`, com `origin=page`
- expoe contador e limite de conversas salvas no frontend

## Admin
- `AssistantConversationAdmin`
- `AssistantMessageAdmin`
- `AssistantActionLogAdmin`
- `AssistantAuditLogAdmin`
- `AssistantUserPreferenceAdmin`

No admin de auditoria:
- filtros por `event_type`, `origin`, classificacoes, status final e motivos
- `list_display` com conversa associada
- `semantic_resolution_json` visivel como campo somente leitura
- ordenacao por data mais recente

## Glossario semantico operacional
Camada central:
- `business_glossary.py` define aliases e jargoes por categoria
- `semantic_resolution.py` transforma esses sinais em uma intencao operacional estruturada

Categorias atuais:
- ranking negativo
- ranking positivo
- produtividade
- improdutividade
- desempenho
- pausa excessiva
- regra de negocio
- ambiguidade

Comportamentos:
- jargoes mapeados para capability/tool args seguros
- termos ambiguos geram esclarecimento curto
- termos dependentes de regra operacional geram resposta transparente sem inventar definicao
- follow-ups reutilizam periodo, sujeito, metrica, polaridade e limite do contexto recente quando apropriado

## Testes
Cobertura em:
- `apps/assistant/tests/test_guardrails.py`
- `apps/assistant/tests/test_capabilities.py`
- `apps/assistant/tests/test_assistant_endpoints.py`
- `apps/assistant/tests/test_assistant_page.py`
- `apps/assistant/tests/test_openai_settings.py`
- `apps/assistant/tests/test_persistence.py`
- `apps/assistant/tests/test_widget_session_endpoints.py`
- `apps/assistant/tests/test_tools_read.py`
- `apps/assistant/tests/test_tools_actions.py`
- `apps/assistant/tests/test_assistant_tool_calling.py`
- `apps/assistant/tests/test_observability.py`

Execucao local sem PostgreSQL remoto:
- `python manage.py test apps.assistant.tests --settings=alive_platform.settings_test`
