# Widget do Assistente (Frontend)

## Arquivos
- Template: `templates/assistant/_assistant_widget.html`
- CSS: `static/assistant/assistant_widget.css`
- JS: `static/assistant/assistant_widget.js`

## Inclusao global
- Incluido no shell: `templates/layouts/base.html`
  - bloco `assistant_widget_assets` (CSS)
  - bloco `assistant_widget` (HTML + JS)
- Excluido no admin:
  - `templates/admin/base.html` sobrescreve os dois blocos vazios.

## Estrutura DOM (IDs estaveis)
- `assistant-fab`
- `assistant-drawer`
- `assistant-close`
- `assistant-messages`
- `assistant-input`
- `assistant-send`
- `assistant-typing`

## Comportamento
- FAB alterna abrir/fechar drawer.
- Botao `X` fecha drawer.
- `Esc` fecha drawer.
- Clique fora do widget fecha drawer.
- Enter envia mensagem; Shift+Enter quebra linha.

## Persistencia local
- Chave de storage:
  - `assistant:conversation:<user_id>`
- `user_id` vem do `data-user-id` no root do widget.
- Ao abrir:
  - se existir `conversation_id`, faz `GET /assistant/conversation/<id>`.
  - se nao existir, mostra estado vazio.

## Envio de mensagem
- Faz `POST /assistant/chat` com:
  - `text`
  - `conversation_id` (quando existente)
- Renderiza mensagem do usuario imediatamente.
- Exibe "Digitando..." enquanto aguarda resposta.
- Salva `conversation_id` retornado no `localStorage`.
