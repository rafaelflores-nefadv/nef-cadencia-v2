# API Interna - Assistant

Base path: `/assistant`

## Autenticacao
Ambos os endpoints exigem usuario autenticado (`@login_required`).

## POST `/assistant/chat`

## Request body
```json
{
  "text": "Quem esta em pausa agora?",
  "conversation_id": 12
}
```

Campos:
- `text` (string, obrigatorio)
- `conversation_id` (int, opcional)

## Response (200)
```json
{
  "conversation_id": 12,
  "answer": "..."
}
```

Comportamentos relevantes:
- cria nova conversa quando `conversation_id` invalido/sem permissao.
- persiste mensagem do usuario e do assistente.
- quando `OPENAI_ENABLED=false`, responde mensagem de assistente desativado.
- quando falta `OPENAI_API_KEY`, responde texto amigavel de configuracao.

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
- sem permissao -> `404`.
