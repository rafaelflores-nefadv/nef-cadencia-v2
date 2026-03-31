from django.db import models
from django.conf import settings

from .choices import ChannelChoices, TemplateTypeChoices


class MessageTemplate(models.Model):
    name = models.CharField(max_length=120, verbose_name="Nome")
    template_type = models.CharField(
        max_length=50,
        choices=TemplateTypeChoices.choices,
        verbose_name="Tipo de template",
    )
    channel = models.CharField(
        max_length=30,
        choices=ChannelChoices.choices,
        verbose_name="Canal",
    )
    subject = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Assunto",
    )
    body = models.TextField(verbose_name="Conteudo")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    version = models.PositiveIntegerField(default=1, verbose_name="Versao")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_message_templates",
        verbose_name="Atualizado por",
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Template de mensagem"
        verbose_name_plural = "Templates de mensagem"
        indexes = [
            models.Index(
                fields=["template_type", "channel", "active"],
                name="idx_msgtpl_type_chan_act",
            ),
        ]

    def __str__(self):
        return f"{self.name} (v{self.version})"
