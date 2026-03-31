# Integrations - Models

## `Integration`
Configura conector por canal de notificacao.

Campos:
- `name`
- `channel` (`chatseguro`, `email`, `webhook`, `slack`, `teams`)
- `enabled`
- `config_json`
- `created_at`, `updated_at`

Indice:
- `(channel, enabled)`

Exemplos de `config_json`:
- email: `from_email`
- webhook: `url`, `timeout_seconds`
