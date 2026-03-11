# Integrations - Fluxos

## Selecionar integracao por canal
```text
Tool de acao (assistant)
     |
     v
consulta Integration(channel, enabled=True)
     |
     v
config_json do conector
```

## Envio de notificacao
```text
Template renderizado
     |
     v
dispatcher por canal
  - chatseguro: stub
  - email: send_mail
  - webhook: HTTP POST
     |
     v
NotificationHistory (SENT/SKIPPED/ERROR)
```
