# Configuracao

## 1) Variaveis de ambiente

## Basicas Django / banco
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

## OpenAI
- `OPENAI_API_KEY`
  - Obrigatoria para usar OpenAI quando `OPENAI_ENABLED=true`.
  - Nao e armazenada em `SystemConfig`.

## Sync legado (monitoring)
- `LEGACY_DRIVER`
- `LEGACY_SERVER`
- `LEGACY_PORT` (opcional)
- `LEGACY_USER`
- `LEGACY_PASSWORD`
- `LEGACY_DATABASE`
- `LEGACY_SCHEMA` (default `dbo`)
- `LEGACY_EVENTS_TABLE` (default `agent_events`)

## 2) Configuracoes via SystemConfig (`rules.SystemConfig`)
As chaves abaixo sao lidas em runtime pelos services:

| Chave | Tipo esperado | Default no codigo | Uso |
|---|---|---|---|
| `OPENAI_ENABLED` | bool | `true` | Liga/desliga chamada a OpenAI no chat |
| `OPENAI_MODEL` | string | `gpt-4.1-mini` | Modelo usado no Responses API |
| `OPENAI_TEMPERATURE` | float/string | `0.2` | Criatividade da resposta |
| `OPENAI_MAX_OUTPUT_TOKENS` | int | `600` | Tamanho maximo da resposta |
| `OPENAI_TIMEOUT_SECONDS` | int | `30` | Timeout no client OpenAI |
| `ASSISTANT_ALLOWED_TEMPLATES_JSON` | json list | `["pause_warning","pause_overflow","supervisor_alert"]` | Allowlist de templates para tools de acao |
| `NOTIFY_THROTTLE_MINUTES` | int | `30` | Janela anti-spam para notificacoes |
| `PAUSE_LIMITS_JSON` | json object | `{}` | Limites por tipo de pausa |
| `PAUSE_LIMIT_DEFAULT_MINUTES` | int | `10` | Limite padrao para overflow |
| `SYNC_LOOKBACK_MINUTES` | int | `180` | Janela do sync legado |
| `LEGACY_SOURCE_NAME` | string | `legacy` | Fonte logica para dedupe |
| `LEGACY_ENABLED` | bool | `true` | Liga/desliga sync legado |

## Tipos (`value_type`) aceitos no model
- `string`
- `int`
- `bool`
- `json`
- `time`

Leitura tipada implementada em `apps/rules/services/system_config.py`:
- `get_config`
- `get_int`
- `get_bool`
- `get_json`
- `get_float`

Os helpers fazem fallback para `default` em valores invalidos.

## 3) Observacoes de seguranca
- Nao gravar segredos sensiveis (ex.: `OPENAI_API_KEY`) no banco.
- Permissoes de actions do assistente sao `staff only`.
- Template livre nao e aceito nas action tools; apenas template permitido + variables.
