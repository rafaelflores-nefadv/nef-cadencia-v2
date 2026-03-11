# Messaging - Models

## `MessageTemplate`
Entidade de template reutilizavel para comunicacao operacional.

Campos relevantes:
- `name`
- `template_type` (ex.: `sem_pausa`, `muitas_pausas`, `supervisor_alerta`)
- `channel` (ex.: `chatseguro`, `email`, `webhook`)
- `subject`
- `body`
- `active`
- `version`
- `updated_by`, `updated_at`

Indice principal:
- `(template_type, channel, active)`

## Choices
Definidos em `apps/messaging/choices.py`:
- `TemplateTypeChoices`
- `ChannelChoices`

## Seed inicial
Migracao `0002_seed_assistant_templates.py` insere templates base para uso do assistente.
