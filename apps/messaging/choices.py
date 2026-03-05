from django.db import models


class TemplateTypeChoices(models.TextChoices):
    SEM_PAUSA = "sem_pausa", "Sem pausa"
    MUITAS_PAUSAS = "muitas_pausas", "Muitas pausas"
    STATUS_IRREGULAR = "status_irregular", "Status irregular"
    SUPERVISOR_ALERTA = "supervisor_alerta", "Supervisor alerta"
    NOTIFICACAO_GENERICA = "notificacao_generica", "Notificacao generica"


class ChannelChoices(models.TextChoices):
    CHATSEGURO = "chatseguro", "ChatSeguro"
    EMAIL = "email", "E-mail"
    TEAMS = "teams", "Microsoft Teams"
    SLACK = "slack", "Slack"
    WEBHOOK = "webhook", "Webhook"
