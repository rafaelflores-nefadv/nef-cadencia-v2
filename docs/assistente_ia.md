# Assistente IA

## Objetivo
Fornecer o assistente operacional Eustacio com:
- identidade fixa como assistente da plataforma,
- validacao de escopo antes do OpenAI,
- validacao de capacidade real antes do modelo responder,
- pos-validacao de saida para escopo e veracidade operacional,
- tool calling controlado apenas para funcionalidades existentes,
- historico persistido por usuario,
- auditoria operacional por solicitacao,
- observabilidade com eventos auditaveis e metricas operacionais,
- preferencia de limite de conversas salvas,
- titulo automatico para conversas,
- widget flutuante com sessao temporaria e salvamento manual,
- pagina dedicada com historico persistido por usuario,
- glossario semantico operacional para jargoes, sinonimos e continuidade,
- fail-safe contra respostas inventadas,
- testes locais sem dependencia de PostgreSQL remoto.

## Escopo vs capacidade
- Escopo responde `isso pertence ao contexto do sistema?`
- Capacidade responde `o sistema realmente consegue consultar, executar ou inferir isso com seguranca?`

Uma solicitacao pode estar:
- fora do escopo: bloqueada pela resposta padrao de escopo
- dentro do escopo, mas fora da capacidade: bloqueada com resposta transparente de funcionalidade nao suportada
- dentro do escopo e da capacidade: segue para tools/modelo com restricoes

## Componentes

## Frontend
- `templates/assistant/_assistant_widget.html`
- `templates/assistant/page.html`
- `static/assistant/assistant_widget.css`
- `static/assistant/assistant_widget.js`
- `static/assistant/assistant_page.css`
- `static/assistant/assistant_page.js`
- `apps/assistant/templatetags/assistant_ui.py`

## Backend
- View: `apps/assistant/views.py`
- Servico principal: `apps/assistant/services/assistant_service.py`
- Config central: `apps/assistant/services/assistant_config.py`
- Guardrails de escopo: `apps/assistant/services/guardrails.py`
- Matriz de capacidades: `apps/assistant/services/capabilities.py`
- Glossario operacional: `apps/assistant/services/business_glossary.py`
- Resolucao semantica: `apps/assistant/services/semantic_resolution.py`
- Persistencia de conversa: `apps/assistant/services/conversation_store.py`
- Auditoria do fluxo: `apps/assistant/services/audit_service.py`
- Codigos e status de observabilidade: `apps/assistant/observability.py`
- Sessao temporaria do widget: `apps/assistant/services/widget_session_service.py`
- Metricas operacionais: `apps/assistant/services/metrics_service.py`
- Prompt do modelo: `apps/assistant/services/system_prompt.py`
- Cliente OpenAI: `apps/assistant/services/openai_client.py`
- Config OpenAI: `apps/assistant/services/openai_settings.py`

## Persistencia
- `AssistantConversation`
- `AssistantMessage`
- `AssistantAuditLog`
- `AssistantUserPreference`
- `AssistantActionLog`

## Fluxo principal
```text
Usuario pergunta
  -> POST /assistant/chat
  -> resolve/cria conversa persistida do usuario
  -> salva mensagem user
  -> atualiza titulo automatico com a primeira mensagem util
  -> resolve_semantic_operational_query(text, contexto_da_conversa)
     -> normaliza jargoes, sinonimos, polaridade, limite e periodo
     -> reaproveita contexto recente quando apropriado
     -> se termo for ambiguo ou depender de regra nao cadastrada: responde com esclarecimento curto
  -> validate_scope(texto_normalizado)
     -> FORA_DO_ESCOPO: resposta padrao de escopo
  -> assess_capability(texto_normalizado)
     -> NAO_SUPORTADA: resposta transparente de funcionalidade nao suportada
     -> CONSULTA_SUPORTADA/ACAO_SUPORTADA: define tools permitidas para a solicitacao
  -> OpenAI Responses API com capability_instruction + tools filtradas
  -> tool calling (quando aplicavel)
  -> evaluate_capability_runtime(...)
     -> SUPORTADA_MAS_SEM_DADOS: resposta transparente de falta de dados
     -> falha de tool: resposta transparente de falha
     -> tool obrigatoria nao executada: resposta de nao confirmacao
  -> validate_assistant_response(...)
  -> validate_operational_truthfulness(...)
  -> salva resposta assistant
  -> registra auditoria do fluxo com classificacoes, tools e status final
  -> retorna conversation_id + answer
```

## Historico, preferencias e auditoria

### AssistantConversation
- representa a conversa do usuario
- guarda `created_by`, `origin`, `status`, `is_persistent`, `title`, `created_at`, `updated_at`
- `origin` diferencia `widget` e `page`
- `status` permite evoluir para arquivamento/exclusao logica sem quebrar auditoria

### AssistantMessage
- guarda cada mensagem da conversa
- `role` aceita `user`, `assistant` e `system`
- o historico continua sendo a base do contexto enviado ao modelo

### AssistantUserPreference
- guarda preferencias por usuario
- atualmente centraliza `max_saved_conversations`
- valor padrao: `100`
- quando o limite e atingido, o sistema nao apaga conversas antigas automaticamente; retorna resposta clara para o usuario

### AssistantAuditLog
- registra cada solicitacao ao Eustacio e eventos operacionais relevantes
- campos principais:
  - `user`
  - `conversation`
  - `origin`
  - `event_type`
  - `input_text`
  - `scope_classification`
  - `capability_classification`
  - `capability_id`
  - `tools_attempted_json`
  - `tools_succeeded_json`
  - `block_reason`
  - `fallback_reason`
  - `final_response_status`
  - `response_text`
  - `semantic_resolution_json`

### semantic_resolution_json
- registra a expressao original e a forma normalizada
- registra `intent`, `business_rule`, `metric`, `subject`, `ranking_order` e `limit`
- informa se houve reaproveitamento de contexto
- informa se houve necessidade de esclarecimento
- informa se a pergunta dependeu de regra operacional ainda nao cadastrada

### Eventos auditados
- `chat_message`
- `page_conversation_created`
- `widget_session_saved`
- `widget_session_ended`
- `conversation_deleted`

### Status finais padronizados
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

### Motivos padronizados
Bloqueio:
- `out_of_scope_phrase`
- `prompt_injection`
- `external_context`
- `no_scope_match`
- `unsupported_pattern`
- `no_capability_match`
- `conversation_limit_reached`
- `empty_widget_session`
- `invalid_widget_session`

Fallback:
- `query_tool_error`
- `action_tool_error`
- `tool_outside_validated_capability`
- `required_query_tool_not_executed`
- `required_query_tool_without_success`
- `supported_without_data`
- `required_action_tool_not_executed`
- `guardrail_output_error`
- `empty_model_output`
- `openai_config_error`
- `openai_runtime_error`
- `assistant_runtime_error`
- `response_out_of_scope_phrase`
- `response_external_context`
- `response_no_scope_match`
- `false_action_claim`
- `false_data_claim`
- `speculative_certainty`

## Widget temporario
- o widget flutuante nao grava historico persistido automaticamente
- as trocas do widget vivem em uma sessao temporaria
- a thread temporaria do widget e identificada por `widget_session_id`
- cada nova pergunta do widget continua na mesma thread enquanto a pagina atual estiver aberta
- fechar no `X`, `Esc`, clique fora ou alternar o FAB apenas oculta o widget
- ao reabrir na mesma pagina, o widget mostra a mesma conversa temporaria
- a conversa temporaria so zera ao recarregar a pagina ou em futuro reset explicito
- a auditoria continua sendo registrada mesmo quando nao existe conversa persistida associada

## Pagina dedicada persistida
- a pagina `/assistant/` usa historico persistido por usuario
- lista apenas conversas do usuario logado
- cada thread persistida e identificada por `conversation_id`
- cada novo envio continua anexando mensagens na conversa ativa
- conversa da pagina nasce com `origin=page`
- a experiencia principal fica dividida em:
  - coluna lateral com historico
  - botao `Nova conversa`
  - painel central com mensagens e composer
- a pagina nao reutiliza a sessao temporaria do widget
- o widget continua com comportamento proprio e separado

## Fluxo de salvar conversa
- o botao `Salvar conversa` cria uma `AssistantConversation` persistida apenas sob demanda
- a conversa e salva com `origin=widget`
- todas as mensagens bem-sucedidas da sessao temporaria sao copiadas para `AssistantMessage`
- o titulo automatico continua vindo da primeira mensagem util do usuario
- se a sessao ja foi salva, o backend retorna a mesma conversa e evita duplicacao
- o evento tambem gera auditoria estruturada em `AssistantAuditLog`

## Regra do titulo automatico
- usa a primeira mensagem util do usuario
- ignora entradas genericas como `oi`, `ola`, `teste`, `bom dia`, `boa tarde` e `boa noite`
- limita o titulo automaticamente
- fallback: `Nova conversa`

## Regra do limite de conversas
- padrao: `100` conversas persistidas por usuario
- o limite e validado antes de criar uma nova conversa persistida
- nenhuma conversa antiga e removida automaticamente
- ao atingir o limite, o chat retorna uma resposta clara e registra auditoria com `blocked_limit`
- a pagina dedicada exibe o contador atual de conversas salvas no frontend

## Matriz de capacidades
Categorias centrais:
- `CONSULTA_SUPORTADA`
- `ACAO_SUPORTADA`
- `NAO_SUPORTADA`
- `SUPORTADA_MAS_SEM_DADOS`

Capacidades suportadas hoje:
- explicar o que o Eustacio consegue fazer
- consultar quem esta em pausa agora
- consultar ranking de pausas por data
- consultar resumo operacional diario
- enviar mensagem suportada para um agente
- notificar supervisores
- consultar ranking de pausas e, em seguida, enviar mensagem para o agente identificado

Exemplos de `NAO_SUPORTADA`:
- prever desempenho futuro
- criar, editar ou remover regras operacionais
- criar relatorios ou dashboards inexistentes
- afirmar alteracoes cadastrais sem tool correspondente

## Validacao de entrada
`guardrails.py` continua responsavel pelo escopo.

Antes do guardrail final, `semantic_resolution.py` tenta traduzir linguagem humana da operacao para uma forma segura.

Exemplos:
- `quem sao os piores agentes de janeiro de 2026?` -> `productivity_analytics_query`, `metric=improductivity`, `ranking_order=worst`, `group_by=agent`, `month=1`, `year=2026`
- `quem esta estourando pausa esse mes?` -> `pause_ranking_query`
- `quem esta se pagando em tempo?` -> `business_rule_query` com `business_rule=se_pagando_em_tempo`

Sinais combinados:
- termos fortes e fracos do dominio
- contexto de plataforma
- intencao operacional
- contexto temporal
- padroes permitidos
- termos externos
- termos de bypass

Depois disso, `capabilities.py` avalia a capacidade real com base em:
- matriz de regex por funcionalidade
- tools realmente disponiveis
- diferenca entre consulta suportada, acao suportada e nao suportada

## Validacao de capacidade
Regras principais:
- se a funcionalidade nao existe, o Eustacio diz isso explicitamente
- se a consulta exige tool real, a resposta so e aceita quando a tool correspondente foi realmente executada
- se a acao exige tool real, o Eustacio so pode afirmar conclusao quando a tool de acao foi executada com sucesso
- tools disponiveis para o modelo sao filtradas pela capacidade validada da solicitacao

## Pos-validacao de saida
Existem duas checagens apos o modelo:

1. Escopo
- `validate_assistant_response(...)`
- bloqueia cultura geral, contexto externo e texto inconsistente

2. Veracidade operacional
- `validate_operational_truthfulness(...)`
- bloqueia resposta que:
  - afirma consulta nao executada
  - afirma envio/execucao nao realizada
  - sugere funcionalidade inexistente
  - usa certeza especulativa

## Observabilidade operacional
Eventos com auditoria estruturada:
- fluxo normal bem-sucedido
- bloqueio por escopo
- recusa por capacidade
- falha de tool
- resposta substituida pela pos-validacao
- fail-safe por erro interno
- criacao de conversa persistida na pagina
- salvamento manual da conversa do widget
- encerramento de sessao temporaria do widget
- exclusao de conversa persistida

Padronizacao:
- `observability.py` centraliza origem, `event_type`, `final_response_status`, motivos e resultado de tool
- `audit_service.py` normaliza os valores antes de gravar no banco
- `AssistantActionLog` continua registrando cada tool individualmente com `success`, `error` ou `denied`
- `AssistantAuditLog.semantic_resolution_json` registra a interpretacao semantica aplicada antes da capability final

Logs:
- o logger `assistant` registra eventos-chave para suporte e diagnostico sem alterar a UX

## Status intermediarios de processamento
O Eustacio agora retorna `processing_statuses` no payload do chat e usa um componente visual de processamento no widget e na pagina dedicada.

Estados internos padronizados:
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

Mapeamento de UI:
- `understanding_query` -> `Entendendo sua pergunta`
- `checking_context` -> `Verificando o contexto da conversa`
- `resolving_intent` -> `Interpretando sua solicitacao`
- `querying_database` -> `Consultando dados no sistema`
- `running_tool` -> `Buscando informacoes`
- `filtering_results` -> `Filtrando os dados para melhor resultado`
- `building_response` -> `Montando a resposta`
- `validating_response` -> `Validando a resposta final`

Regras:
- o backend so emite etapas que realmente aconteceram
- perguntas fora do escopo nao emitem `querying_database`
- consultas com tool real podem emitir `querying_database`, `running_tool` e `filtering_results`
- em falha operacional, o trace termina em `failed`

Frontend:
- o widget e a pagina dedicada substituem `Digitando...` por um indicador de processamento discreto
- durante a requisicao, o frontend usa uma sequencia fallback elegante
- quando o backend devolve a resposta, o estado de processamento e removido
- o processing state e estritamente efemero e pertence apenas a requisicao ativa no frontend
- `processing_status` e `processing_statuses` servem para auditoria e renderizacao transitória da resposta corrente, nunca para restaurar `Pensando...` em refresh, reabertura do widget ou troca de conversa
- fechar o widget limpa o estado visual de processamento, mas preserva a conversa temporaria da pagina atual
- reabrir o widget ou trocar de conversa nunca deve restaurar um status visual de request antiga
- recarregar a pagina recria tudo do zero e descarta a conversa temporaria do widget
- timers e transicoes do componente sao invalidados quando a requisicao termina, falha ou perde relevancia para a UI atual
- o atributo `hidden` do componente de processing precisa permanecer soberano no estado inicial; restaurar thread ou abrir o widget sem request ativa nao pode exibir `Pensando...`

Transicoes visuais:
- fade in ao iniciar
- crossfade de texto entre estados
- fade out ao concluir
- indicador pulsante discreto no dark theme
- fallback progressivo apenas enquanto a promise da requisicao estiver ativa

Metricas disponiveis em backend:
- `get_assistant_metrics(user=...)`
- `messages_total`
- `saved_conversations_total`
- `interactions_by_origin`
- `events_by_type`
- `blocked_scope_total`
- `blocked_capability_total`
- `tool_failures_total`
- `fallbacks_total`
- `successful_responses_total`

Consulta administrativa:
- `AssistantAuditLogAdmin` expõe `event_type`, `origin`, `conversation`, motivos e status final
- a ordenacao padrao no admin fica da mais recente para a mais antiga

## Comportamento transparente
Quando nao ha dados:
- o Eustacio informa que nao encontrou dados suficientes no sistema

Quando a funcionalidade nao existe:
- o Eustacio informa que nao possui essa funcionalidade no ambiente atual

Quando a tool falha:
- o Eustacio informa que nao foi possivel concluir a consulta ou a acao naquele momento

Quando a resposta nao pode ser comprovada:
- o Eustacio informa que nao consegue confirmar a informacao com seguranca a partir do que foi realmente executado

## Fail-safe contra invencao
O assistente bloqueia respostas que aparentem:
- ter consultado dados sem tool de consulta
- ter enviado/notificado sem tool de acao bem-sucedida
- ter criado, alterado, atualizado ou gerado algo que o sistema nao suporta
- ter certeza sobre previsoes ou hipoteses

## Glossario semantico operacional
Arquivos:
- `apps/assistant/services/business_glossary.py`
- `apps/assistant/services/semantic_resolution.py`

Conceitos cobertos:
- ranking positivo e negativo
- produtividade, improdutividade e desempenho
- pausa excessiva
- regras de negocio dependentes de definicao operacional
- termos ambiguos que exigem esclarecimento

Exemplos de expressoes entendidas:
- `piores agentes`
- `melhores agentes`
- `quem esta rendendo bem`
- `quem esta com produtividade fraca`
- `quem esta com ocioso alto`
- `quem esta estourando pausa`
- `quem esta compensando a operacao`
- `quem esta valendo o custo`

Tratamento de ambiguidades:
- termos como `quem esta ruim?`, `quem esta folgado?`, `quem esta forte?` nao geram resposta inventada
- o Eustacio responde com um esclarecimento curto pedindo o criterio operacional correto

Regras de negocio:
- `se_pagando_em_tempo`
- `segurando_meta`

Quando a regra ainda nao esta definida:
- o Eustacio reconhece o termo como valido no dominio
- nao inventa definicao
- pede confirmacao ou informa que ainda precisa da regra operacional cadastrada

Hierarquia de resolucao:
1. periodo explicito atual
2. sujeito explicito atual
3. termo/regra explicita atual
4. contexto recente da conversa
5. default seguro
6. pedido de esclarecimento

## Respostas institucionais relevantes
Centralizadas em `assistant_config.py`:
- `ASSISTANT_OUT_OF_SCOPE_RESPONSE`
- `ASSISTANT_CAPABILITIES_RESPONSE`
- `ASSISTANT_UNSUPPORTED_CAPABILITY_RESPONSE`
- `ASSISTANT_NO_DATA_RESPONSE`
- `ASSISTANT_QUERY_FAILURE_RESPONSE`
- `ASSISTANT_ACTION_FAILURE_RESPONSE`
- `ASSISTANT_UNVERIFIED_RESPONSE`

## Prompt do modelo
`system_prompt.py` reforca que o modelo:
- nao pode inventar dados
- nao pode fingir execucao
- nao pode afirmar acesso a informacoes nao consultadas
- deve dizer explicitamente quando nao ha dados
- deve dizer explicitamente quando a funcionalidade nao existe

## Tools de leitura
- `get_pause_ranking(date, limit=10, pause_type=None)`
- `get_current_pauses(pause_type=None)`
- `get_day_summary(date)`

## Tools de acao
- `send_message_to_agent(agent_id, template_key, channel, variables)`
- `notify_supervisors(template_key, channel, variables)`

## Guardrails de acao
- `staff only`
- sem texto livre para notificacoes
- allowlist de templates via `ASSISTANT_ALLOWED_TEMPLATES_JSON`
- throttle via `NOTIFY_THROTTLE_MINUTES`
- auditoria em `AssistantActionLog`

## Configuracao centralizada
Edite `apps/assistant/services/assistant_config.py` para alterar:
- nome do assistente
- respostas transparentes
- titulo padrao e limite padrao de conversas
- resumo das capacidades suportadas
- sinais de escopo
- termos de alegacao falsa de dados/acao
- termos de certeza especulativa

## Testes
Cobertura principal:
- `apps/assistant/tests/test_guardrails.py`
- `apps/assistant/tests/test_capabilities.py`
- `apps/assistant/tests/test_assistant_endpoints.py`
- `apps/assistant/tests/test_assistant_page.py`
- `apps/assistant/tests/test_assistant_tool_calling.py`
- `apps/assistant/tests/test_persistence.py`
- `apps/assistant/tests/test_widget_session_endpoints.py`
- `apps/assistant/tests/test_observability.py`
- `apps/assistant/tests/test_tools_read.py`
- `apps/assistant/tests/test_tools_actions.py`
- `apps/assistant/tests/test_openai_settings.py`

## Estrategia de mocks nos testes
- OpenAI sempre mockado nos testes de endpoint/integracao do assistant
- tool calling mockado quando o objetivo do teste e o fluxo do assistant
- sem dependencia de rede externa
- sem dependencia do PostgreSQL remoto
- banco local de teste via SQLite em `alive_platform/settings_test.py`
- auditoria e metricas exercitadas com fixtures locais, mocks de OpenAI e mocks de tool calling

## Como executar os testes localmente
```bash
python manage.py test apps.assistant.tests --settings=alive_platform.settings_test
```

Esse comando:
- usa SQLite em memoria
- evita o PostgreSQL remoto do `.env`
- mantem execucao deterministica em ambiente local/CI
