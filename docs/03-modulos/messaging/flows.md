# Messaging - Fluxos

## Fluxo de uso de template
```text
Tool de acao (assistant)
     |
     v
resolve template ativo por tipo/canal
     |
     v
render subject/body com variaveis
     |
     v
dispatch no canal (email/webhook/chat stub)
     |
     v
NotificationHistory
```

## Fluxo de manutencao de templates
```text
Admin Django
     |
     v
CRUD MessageTemplate
     |
     v
templates disponiveis para tools
```
