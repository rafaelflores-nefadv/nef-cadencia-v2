# Pagina Dedicada do Eustacio

## Arquivos
- Template: `templates/assistant/page.html`
- CSS: `static/assistant/assistant_page.css`
- JS: `static/assistant/assistant_page.js`

## Objetivo
- oferecer a experiencia persistida do Eustacio
- separar claramente o historico salvo da sessao temporaria do widget
- manter o visual dark do sistema e a navegacao pelo menu lateral

## Layout
- coluna lateral com historico do usuario
- botao `Nova conversa`
- contador `conversas salvas / limite`
- painel principal com mensagens
- composer para envio
- estado vazio amigavel quando nenhuma conversa estiver selecionada

## Fluxo do frontend
- `GET /assistant/`
  - renderiza a pagina e o estado inicial
- `GET /assistant/conversations`
  - lista conversas persistidas do usuario
- `POST /assistant/conversations`
  - cria nova conversa persistida com `origin=page`
- `GET /assistant/conversations/<id>`
  - carrega mensagens da conversa selecionada
- `POST /assistant/conversations/<id>/delete`
  - exclui logicamente a conversa
- `POST /assistant/chat`
  - envia mensagem usando o fluxo seguro do assistente com `origin=page`
  - sempre vinculado ao `conversation_id` ativo
  - devolve a conversa atualizada com o historico completo da thread

## Diferenca para o widget
- widget:
  - sessao temporaria
  - nao salva automaticamente
  - usa `widget_session_id` como identificador da thread
  - fechar apenas oculta; refresh descarta
- pagina:
  - historico persistido por usuario
  - cria conversa persistida
  - usa `conversation_id` como identificador da thread
  - conversa continua disponivel na lista lateral

## Limite de conversas
- o frontend exibe `conversation_count` e `conversation_limit`
- quando o limite e atingido:
  - o botao `Nova conversa` fica desabilitado
  - a API retorna mensagem clara
  - o usuario precisa excluir uma conversa antiga para liberar espaco
