# Widget do Assistente (Frontend)

## Arquivos
- Template: `templates/assistant/_assistant_widget.html`
- CSS: `static/assistant/assistant_widget.css`
- JS: `static/assistant/assistant_widget.js`
- UI strings: `apps/assistant/templatetags/assistant_ui.py`

## Inclusao global
- Incluido no shell: `templates/layouts/base.html`
  - bloco `assistant_widget_assets` (CSS)
  - bloco `assistant_widget` (HTML + JS)
- Na pagina dedicada `/assistant/`, o widget e omitido para evitar sobreposicao com a experiencia persistida.
- Excluido no admin:
  - `templates/admin/base.html` sobrescreve os dois blocos vazios.

## Estrutura DOM (IDs estaveis)
- `assistant-fab`
- `assistant-drawer`
- `assistant-save`
- `assistant-close`
- `assistant-messages`
- `assistant-input`
- `assistant-send`
- `assistant-typing`

## Comportamento
- FAB alterna abrir/fechar drawer.
- Botao `Salvar conversa` persiste a sessao temporaria atual sob demanda.
- Botao `X` fecha drawer sem apagar a conversa temporaria.
- `Esc` fecha drawer sem apagar a conversa temporaria.
- Clique fora do widget fecha drawer sem apagar a conversa temporaria.
- Enter envia mensagem; Shift+Enter quebra linha.
- O widget apresenta o assistente como Eustacio e reforca o escopo operacional na mensagem vazia.
- Ao reabrir na mesma pagina, o widget reaproveita a mesma conversa temporaria.

## Sessao temporaria
- O widget nao usa mais `localStorage` para historico.
- O frontend gera um `widget_session_id` temporario.
- O backend usa esse identificador para manter o contexto temporario da sessao atual.
- `widget_session_id` e a fonte da verdade da thread temporaria do widget.
- Enquanto a pagina atual permanecer aberta, novas perguntas continuam anexadas na mesma thread.
- Fechar o widget apenas oculta a UI e limpa o status efemero da requisicao ativa.
- A conversa temporaria permanece viva enquanto a pagina atual estiver aberta.
- Recarregar a pagina recria o widget do zero e descarta a conversa temporaria anterior.
- Auditoria continua existindo mesmo sem conversa persistida.
- A pagina dedicada do Eustacio usa outro fluxo: historico persistido por usuario.

## Envio de mensagem
- Faz `POST /assistant/widget/chat` com:
  - `text`
  - `widget_session_id`
- Renderiza mensagem do usuario imediatamente.
- O backend devolve a thread temporaria atualizada para manter frontend e servidor sincronizados.
- Exibe um status de processamento apenas durante a requisicao ativa.
- O status nao deve aparecer no load inicial, ao apenas abrir o widget ou ao reabrir o widget.
- O CSS do componente precisa respeitar explicitamente o atributo `hidden`; restaurar thread nunca deve tornar o status visivel.
- Nao persiste historico automaticamente.

## Salvar conversa
- Faz `POST /assistant/widget/session/save` com `widget_session_id`.
- Se a sessao ainda nao foi salva:
  - cria `AssistantConversation` persistida
  - copia as mensagens temporarias
  - marca `origin=widget`
- Se a sessao ja foi salva:
  - o backend retorna a mesma conversa
  - o botao permanece desabilitado para evitar duplicacao

## Encerrar sessao
- Faz `POST /assistant/widget/session/end` com `widget_session_id`.
- Esse endpoint nao e usado no simples fechar visual do drawer.
- Ele deve ser reservado para reset/encerramento explicito de sessao, quando houver esse fluxo.
