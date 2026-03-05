# Estrutura do Projeto

## Arvore principal (estado atual)
```text
nef-cadencia-v2/
|-- alive_platform/
|   |-- settings.py
|   |-- urls.py
|   |-- asgi.py
|   `-- wsgi.py
|
|-- apps/
|   |-- accounts/
|   |-- assistant/
|   |-- integrations/
|   |-- messaging/
|   |-- monitoring/
|   |-- reports/
|   `-- rules/
|
|-- templates/
|   |-- layouts/
|   |-- assistant/
|   |-- monitoring/
|   |-- accounts/
|   |-- admin/
|   `-- partials/
|
|-- static/
|   |-- css/
|   |-- js/
|   `-- assistant/
|
|-- assets/
|   `-- tailwind.css
|
|-- docs/
|   |-- README.md
|   |-- arquitetura.md
|   |-- estrutura_do_projeto.md
|   |-- configuracao.md
|   |-- deploy.md
|   |-- assistente_ia.md
|   |-- modules/
|   |-- frontend/
|   |-- api/
|   `-- SYNC.md
|
|-- manage.py
|-- requirements.txt
|-- package.json
|-- tailwind.config.js
`-- postcss.config.js
```

## Responsabilidade por app
- `apps/accounts`: autenticacao e contexto auxiliar para templates do admin.
- `apps/assistant`: conversas, mensagens, logs de acao, OpenAI e tools.
- `apps/monitoring`: entidades operacionais (agent/event/stats/job/notificacao), dashboard e sync legado.
- `apps/messaging`: templates e enums de tipo/canal.
- `apps/integrations`: integracoes habilitadas por canal.
- `apps/rules`: parametros dinamicos em `SystemConfig` e helpers de leitura tipada.
- `apps/reports`: app reservado, sem uso funcional no estado atual.

## Padrao de services
- Services ficam em `apps/<modulo>/services/`.
- `rules/services/system_config.py`: API padrao para leitura de config tipada.
- `assistant/services/*`: orquestracao de chat, cliente OpenAI, settings, tools e registry.
- `monitoring/services/legacy_sync_service.py`: encapsula sync incremental do legado.

## Padrao de templates
- Shell principal: `templates/layouts/base.html`.
- Admin: `templates/admin/base.html` estende o shell e desabilita widget do assistente.
- Conteudo funcional:
  - `templates/dashboard.html`
  - `templates/monitoring/*.html`
  - `templates/accounts/login.html`
  - `templates/assistant/_assistant_widget.html`

## Static assets
- CSS principal compilado: `static/css/app.css`.
- JS principal de shell/menu: `static/js/app.js`.
- Widget IA:
  - `static/assistant/assistant_widget.css`
  - `static/assistant/assistant_widget.js`

## Rotas ativas
- Root:
  - `/` -> redirect para `dashboard`
  - `/admin/`
- Accounts:
  - `/login`
  - `/logout`
- Monitoring:
  - `/dashboard`
  - `/agents`
  - `/agents/<id>`
  - `/runs`
  - `/runs/<id>`
- Assistant:
  - `/assistant/chat`
  - `/assistant/conversation/<id>`
