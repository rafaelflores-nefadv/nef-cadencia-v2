# Rules - Services

## `system_config.py`
API tipada para leitura de configuracoes:
- `get_config`
- `get_int`
- `get_bool`
- `get_json`
- `get_float`

Caracteristicas:
- fallback para default quando chave ausente/invalida
- parse de tipos baseado em `SystemConfig.value_type`
- isolamento de parsing para reduzir duplicacao em outros modulos

Consumidores principais:
- `assistant.openai_settings`
- `assistant.tools_actions`
- `monitoring.sync_legacy_events`
- `assistant.tools_read`
