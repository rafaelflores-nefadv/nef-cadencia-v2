from django.db import models

from apps.messaging.choices import ChannelChoices


class Integration(models.Model):
    name = models.CharField(max_length=120, verbose_name="Nome")
    channel = models.CharField(
        max_length=30,
        choices=ChannelChoices.choices,
        verbose_name="Canal",
    )
    enabled = models.BooleanField(default=True, verbose_name="Habilitada")
    config_json = models.JSONField(default=dict, verbose_name="Configuracao JSON")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Integracao"
        verbose_name_plural = "Integracoes"
        indexes = [
            models.Index(fields=["channel", "enabled"], name="idx_integ_channel_en"),
        ]

    def __str__(self):
        return f"{self.name} ({self.channel})"
