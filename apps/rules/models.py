from django.db import models
from django.conf import settings


class SystemConfigValueType(models.TextChoices):
    STRING = "string", "String"
    INT = "int", "Inteiro"
    BOOL = "bool", "Booleano"
    JSON = "json", "JSON"
    TIME = "time", "Horario"


class SystemConfig(models.Model):
    config_key = models.CharField(max_length=100, unique=True, verbose_name="Chave")
    config_value = models.TextField(verbose_name="Valor")
    value_type = models.CharField(
        max_length=20,
        choices=SystemConfigValueType.choices,
        verbose_name="Tipo do valor",
    )
    description = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Descricao",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_system_configs",
        verbose_name="Atualizado por",
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Configuracao do sistema"
        verbose_name_plural = "Configuracoes do sistema"
        ordering = ["config_key"]

    def __str__(self):
        return self.config_key
