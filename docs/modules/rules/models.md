# Rules - Models

## `SystemConfig`
Tabela de configuracao central para parametros operacionais.

Campos:
- `config_key` (unico)
- `config_value`
- `value_type` (`string`, `int`, `bool`, `json`, `time`)
- `description`
- `updated_by`
- `updated_at`

Uso pratico:
- parametros de OpenAI (`OPENAI_*`)
- parametros de throttling/notificacao
- parametros de sync legado (`SYNC_*`, `LEGACY_*`)
- limites operacionais (`PAUSE_LIMITS_JSON`, etc.)
