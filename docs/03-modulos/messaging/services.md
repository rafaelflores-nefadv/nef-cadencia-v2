# Messaging - Services

No estado atual, o app `messaging` nao possui camada `services` propria.

A logica de uso de templates ocorre principalmente em:
- `apps.assistant.services.tools_actions`
  - resolve template ativo por tipo/canal
  - renderiza `subject/body` com variaveis
  - encaminha para dispatcher de canal

Dependencias do fluxo:
- `rules` (config de templates permitidos)
- `integrations` (conector por canal)
- `monitoring.NotificationHistory` (auditoria)
