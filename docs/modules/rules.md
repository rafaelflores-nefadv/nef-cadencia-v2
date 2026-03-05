# Modulo Rules

## Escopo
Centralizar configuracoes globais dinamicas no banco.

## Model
- `SystemConfig` (`apps/rules/models.py`)
  - `config_key` (unique)
  - `config_value`
  - `value_type` (`string|int|bool|json|time`)
  - `description`
  - `updated_by`
  - `updated_at`

## Service de leitura tipada
Arquivo: `apps/rules/services/system_config.py`

Funcoes disponiveis:
- `get_config(key, default=None)`
- `get_int(key, default)`
- `get_bool(key, default)`
- `get_json(key, default)`
- `get_float(key, default)`

Comportamento:
- retorna `default` quando chave nao existe.
- respeita `value_type` no parse.
- valor invalido nao quebra fluxo; retorna `default`.

## Modulos que dependem de rules
- `assistant`
  - configuracao OpenAI
  - allowlist de templates
  - throttle
  - limites de pausa
- `monitoring`
  - parametros do sync legado

## Admin
- `SystemConfigAdmin` registrado em `apps/rules/admin.py`.

## Testes
- `apps/rules/tests/test_system_config_service.py`
