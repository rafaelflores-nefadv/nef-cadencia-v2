# Modulo Integrations

## Escopo
Configurar destinos de integracao por canal para notificacoes.

## Model
- `Integration` (`apps/integrations/models.py`)
  - `name`
  - `channel`
  - `enabled`
  - `config_json`
  - `created_at`
  - `updated_at`

## Uso atual no assistente
`apps/assistant/services/tools_actions.py` consulta integracao ativa por canal:
- sem integracao: notificacao marcada como `SKIPPED` (queued).
- com integracao:
  - `chatseguro`: envio stub com status de sucesso.
  - `email`: tentativa via `send_mail` (depende de `from_email` em `config_json`).
  - `webhook`: POST HTTP via `urllib` para `config_json.url`.
  - `slack`/`teams`: marcado como queued/not implemented no estado atual.

## Admin
- `IntegrationAdmin` registrado em `apps/integrations/admin.py`.

## Observacao
Nao existe `urls.py` para o app `integrations`; configuracao e feita via admin/model.
