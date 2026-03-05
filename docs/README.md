# NEF Cadencia v2 - Documentacao Tecnica

## Visao geral
Aplicacao Django server-side para operacao de monitoramento (agentes/eventos/jobs) e assistente operacional com OpenAI + tool calling.

Esta documentacao foi atualizada com base no codigo atual em:
- `alive_platform/settings.py`
- `alive_platform/urls.py`
- `apps/*`
- `templates/*`
- `static/*`

## Modulos principais
- `assistant`: chat, historico, OpenAI Responses API, tools de leitura e de acao com auditoria.
- `monitoring`: dashboard, agentes, eventos, estatisticas diarias, historico de notificacoes e job runs.
- `messaging`: templates de mensagem por tipo e canal.
- `integrations`: configuracao de integracoes por canal.
- `rules`: configuracoes dinamicas (`SystemConfig`) e helpers tipados.
- `accounts`: login/logout e context processor para o admin.
- `reports`: app instalado, sem modelos/views ativos no estado atual.

## Stack tecnologica
- Python 3
- Django 4.2.16
- PostgreSQL (`psycopg`)
- `django-environ`
- OpenAI SDK (`openai`)
- Templates Django
- Tailwind CLI + PostCSS (build de `static/css/app.css`)
- JavaScript vanilla (`static/js/app.js` e `static/assistant/assistant_widget.js`)

## Fluxo geral
```text
Usuario autenticado
  -> Pagina Django (dashboard/agents/runs/admin)
  -> Widget global do assistente (fora do admin)
  -> POST /assistant/chat
  -> Assistant Service
  -> OpenAI Responses API (gpt-4.1-mini por default)
  -> Tool calling
  -> Monitoring / Messaging / Integrations / Rules
```

## Execucao local
```bash
pip install -r requirements.txt
npm install
python manage.py migrate
npm run build:css
python manage.py runserver
```

## Mapa da documentacao
- `docs/arquitetura.md`
- `docs/estrutura_do_projeto.md`
- `docs/configuracao.md`
- `docs/deploy.md`
- `docs/assistente_ia.md`
- `docs/modules/assistant.md`
- `docs/modules/monitoring.md`
- `docs/modules/messaging.md`
- `docs/modules/integrations.md`
- `docs/modules/rules.md`
- `docs/frontend/widget_assistente.md`
- `docs/api/assistant_api.md`
- `docs/SYNC.md` (detalhes do comando `sync_legacy_events`)
