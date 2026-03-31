# Arquitetura do Sistema

## Visao macro
O projeto segue arquitetura monolitica modular em Django, com separacao por apps de dominio e renderizacao server-side via templates.

## Camadas
1. Core Django (`alive_platform`)
- `settings.py`: apps, banco, middleware, templates, static.
- `urls.py`: roteamento raiz.

2. Apps de dominio (`apps`)
- `assistant`, `monitoring`, `messaging`, `integrations`, `rules`, `accounts`, `reports`.

3. Persistencia
- PostgreSQL.
- ORM Django.
- Modelos de operacao em `monitoring`.
- Configuracao dinamica em `rules.SystemConfig`.

4. Frontend server-side
- `templates/layouts/base.html` como shell principal.
- Widgets/partials em templates dedicados.
- CSS principal em `static/css/app.css`.
- JS de shell em `static/js/app.js`.

5. Assistente IA
- Widget global: `templates/assistant/_assistant_widget.html`.
- Endpoint: `/assistant/chat`.
- Servico de orquestracao: `apps/assistant/services/assistant_service.py`.
- Integracao OpenAI: `apps/assistant/services/openai_client.py`.
- Tool calling: `tool_registry.py`, `tools_read.py`, `tools_actions.py`.

## Diagrama de fluxo do assistente
```text
User
  -> Widget Assistente
  -> /assistant/chat
  -> Assistant Service
  -> OpenAI (gpt-4.1-mini por default)
  -> Tools
  -> Monitoring / Messaging / Integrations / Rules
```

## Fluxo de dados (chat com tool calling)
```text
POST /assistant/chat
  -> salva mensagem do usuario (AssistantMessage)
  -> monta contexto (ultimas 10 mensagens + system prompt)
  -> chama Responses API
  -> se houver function_call:
       executa tool via registry
       audita em AssistantActionLog
       envia function_call_output para a OpenAI
       repete (limite 3 tools por request)
  -> salva resposta final do assistente
  -> retorna {conversation_id, answer}
```

## Integracoes externas
- OpenAI Responses API (SDK oficial `openai`).
- Webhook HTTP via `urllib` para notificacoes.
- Email via `django.core.mail.send_mail`.
- Conector legado ODBC (`pyodbc`) no sync de monitoring.

## Componente de sincronizacao legado
```text
python manage.py sync_legacy_events
  -> JobRun RUNNING
  -> LegacySyncService consulta legado (janela movel)
  -> upsert Agent / AgentEvent
  -> recalcula AgentDayStats por agente+dia afetado
  -> JobRun SUCCESS ou ERROR
```
