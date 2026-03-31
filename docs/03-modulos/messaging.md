# Modulo Messaging

## Escopo
Gerenciar templates de comunicacao usados pelas rotinas operacionais e pelo assistente.

## Model
- `MessageTemplate` (`apps/messaging/models.py`)
  - `name`
  - `template_type`
  - `channel`
  - `subject`
  - `body`
  - `active`
  - `version`
  - `updated_by`
  - `updated_at`

## Choices (`apps/messaging/choices.py`)
- Tipos (`TemplateTypeChoices`):
  - `sem_pausa`
  - `muitas_pausas`
  - `status_irregular`
  - `supervisor_alerta`
  - `notificacao_generica`
- Canais (`ChannelChoices`):
  - `chatseguro`
  - `email`
  - `teams`
  - `slack`
  - `webhook`

## Integracao com assistant actions
- `tools_actions.py` busca template ativo por:
  - `template_type` (derivado de `template_key`)
  - `channel`
- Renderiza `subject/body` via template engine Django + `variables`.

## Seed de templates
- Migration: `apps/messaging/migrations/0002_seed_assistant_templates.py`
- Templates criados/atualizados:
  - `pause_overflow`
  - `pause_warning`
  - `supervisor_alert`

## Admin
- `MessageTemplateAdmin` registrado em `apps/messaging/admin.py`.
