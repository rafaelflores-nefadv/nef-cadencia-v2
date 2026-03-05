from django.db import models
from django.utils import timezone

from apps.messaging.choices import ChannelChoices, TemplateTypeChoices


class NotificationStatusChoices(models.TextChoices):
    SENT = "SENT", "Enviado"
    ERROR = "ERROR", "Erro"
    SKIPPED = "SKIPPED", "Ignorado"


class JobNameChoices(models.TextChoices):
    SYNC = "sync", "Sincronizacao"
    CADENCIA = "cadencia", "Cadencia"
    IRREGULARES = "irregulares", "Irregulares"
    NOTIFICACOES = "notificacoes", "Notificacoes"
    RELATORIOS = "relatorios", "Relatorios"


class JobRunStatusChoices(models.TextChoices):
    RUNNING = "RUNNING", "Em execucao"
    SUCCESS = "SUCCESS", "Sucesso"
    ERROR = "ERROR", "Erro"


class Agent(models.Model):
    cd_operador = models.PositiveIntegerField(unique=True, verbose_name="Codigo do operador")
    nm_agente = models.CharField(max_length=100, null=True, blank=True, verbose_name="Nome")
    nm_agente_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Codigo do agente",
    )
    nr_ramal = models.CharField(max_length=50, null=True, blank=True, verbose_name="Ramal")
    email = models.EmailField(null=True, blank=True, verbose_name="E-mail")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Agente"
        verbose_name_plural = "Agentes"
        ordering = ["cd_operador"]

    def __str__(self):
        return f"{self.cd_operador} - {self.nm_agente or 'Sem nome'}"


class AgentEvent(models.Model):
    source = models.CharField(
        max_length=30,
        default="legacy",
        db_index=True,
        verbose_name="Fonte",
    )
    source_event_hash = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name="Hash do evento na fonte",
    )
    ext_event = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Evento externo",
    )
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Agente",
    )
    cd_operador = models.PositiveIntegerField(db_index=True, verbose_name="Codigo do operador")
    tp_evento = models.CharField(max_length=50, db_index=True, verbose_name="Tipo do evento")
    nm_pausa = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Nome da pausa",
    )
    dt_inicio = models.DateTimeField(db_index=True, verbose_name="Data/hora de inicio")
    dt_fim = models.DateTimeField(null=True, blank=True, verbose_name="Data/hora de fim")
    duracao_seg = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Duracao em segundos",
    )
    dt_captura_origem = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data/hora de captura na origem",
    )
    raw_payload = models.JSONField(null=True, blank=True, verbose_name="Payload bruto")
    inserted_at = models.DateTimeField(auto_now_add=True, verbose_name="Inserido em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Evento de agente"
        verbose_name_plural = "Eventos de agentes"
        constraints = [
            models.UniqueConstraint(
                fields=["source", "source_event_hash"],
                name="uniq_agentevent_source_hash",
            ),
            models.UniqueConstraint(
                fields=["source", "ext_event"],
                condition=models.Q(ext_event__isnull=False),
                name="uq_agentevent_source_extevent",
            ),
            models.CheckConstraint(
                check=models.Q(duracao_seg__isnull=True) | models.Q(duracao_seg__gte=0),
                name="chk_agentevent_duracao_nonneg",
            ),
        ]
        indexes = [
            models.Index(fields=["agent", "dt_inicio"], name="idx_agevent_agent_dtini"),
        ]

    def __str__(self):
        return f"{self.cd_operador} - {self.tp_evento} ({self.dt_inicio})"


class AgentWorkday(models.Model):
    source = models.CharField(max_length=50, verbose_name="Fonte")
    ext_event = models.BigIntegerField(verbose_name="Evento externo")
    cd_operador = models.PositiveIntegerField(verbose_name="Codigo do operador")
    nm_operador = models.CharField(max_length=255, verbose_name="Nome do operador")
    work_date = models.DateField(verbose_name="Data de trabalho")
    dt_inicio = models.DateTimeField(verbose_name="Data/hora de inicio")
    dt_fim = models.DateTimeField(verbose_name="Data/hora de fim")
    duracao_seg = models.IntegerField(verbose_name="Duracao em segundos")
    dt_captura_origem = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data/hora de captura na origem",
    )
    raw_payload = models.JSONField(default=dict, blank=True, verbose_name="Payload bruto")
    inserted_at = models.DateTimeField(auto_now_add=True, verbose_name="Inserido em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        db_table = "monitoring_agent_workday"
        verbose_name = "Jornada diaria do agente"
        verbose_name_plural = "Jornadas diarias dos agentes"
        constraints = [
            models.UniqueConstraint(
                fields=["source", "cd_operador", "work_date"],
                name="uq_workday_source_operador_date",
            ),
            models.UniqueConstraint(
                fields=["source", "ext_event"],
                name="uq_workday_source_extevent",
            ),
        ]
        indexes = [
            models.Index(fields=["source", "work_date"], name="idx_workday_source_date"),
            models.Index(fields=["cd_operador", "work_date"], name="idx_workday_operador_date"),
        ]

    def __str__(self):
        return f"{self.cd_operador} - {self.work_date}"


class AgentDayStats(models.Model):
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name="day_stats",
        verbose_name="Agente",
    )
    cd_operador = models.PositiveIntegerField(db_index=True, verbose_name="Codigo do operador")
    data_ref = models.DateField(db_index=True, verbose_name="Data de referencia")
    qtd_pausas = models.PositiveIntegerField(default=0, verbose_name="Quantidade de pausas")
    tempo_pausas_seg = models.PositiveIntegerField(
        default=0,
        verbose_name="Tempo de pausas em segundos",
    )
    ultima_pausa_inicio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ultimo inicio de pausa",
    )
    ultima_pausa_fim = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ultimo fim de pausa",
    )
    ultimo_logon = models.DateTimeField(null=True, blank=True, verbose_name="Ultimo logon")
    ultimo_logoff = models.DateTimeField(null=True, blank=True, verbose_name="Ultimo logoff")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Estatistica diaria do agente"
        verbose_name_plural = "Estatisticas diarias dos agentes"
        constraints = [
            models.UniqueConstraint(
                fields=["agent", "data_ref"],
                name="uniq_agentdaystats_agent_date",
            ),
        ]
        indexes = [
            models.Index(fields=["agent", "data_ref"], name="idx_agday_agent_data"),
        ]

    def __str__(self):
        return f"{self.cd_operador} - {self.data_ref}"


class NotificationHistory(models.Model):
    agent = models.ForeignKey(
        Agent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_history",
        verbose_name="Agente",
    )
    cd_operador = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Codigo do operador",
    )
    notification_type = models.CharField(
        max_length=50,
        choices=TemplateTypeChoices.choices,
        verbose_name="Tipo de notificacao",
    )
    channel = models.CharField(
        max_length=30,
        choices=ChannelChoices.choices,
        verbose_name="Canal",
    )
    recipient = models.CharField(max_length=200, verbose_name="Destinatario")
    template = models.ForeignKey(
        "messaging.MessageTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_history",
        verbose_name="Template",
    )
    status = models.CharField(
        max_length=20,
        choices=NotificationStatusChoices.choices,
        verbose_name="Status",
    )
    error_message = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name="Mensagem de erro",
    )
    payload = models.JSONField(null=True, blank=True, verbose_name="Payload")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Historico de notificacao"
        verbose_name_plural = "Historico de notificacoes"
        indexes = [
            models.Index(
                fields=["agent", "notification_type", "created_at"],
                name="idx_nothist_agent_type_dt",
            ),
            models.Index(fields=["status", "created_at"], name="idx_nothist_status_dt"),
        ]

    def __str__(self):
        return f"{self.notification_type} - {self.channel} - {self.status}"


class NotificationThrottle(models.Model):
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name="notification_throttles",
        verbose_name="Agente",
    )
    notification_type = models.CharField(
        max_length=50,
        choices=TemplateTypeChoices.choices,
        verbose_name="Tipo de notificacao",
    )
    last_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ultimo envio em",
    )
    sent_count_today = models.PositiveIntegerField(default=0, verbose_name="Envios hoje")
    day_ref = models.DateField(default=timezone.localdate, verbose_name="Dia de referencia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Controle de notificacao"
        verbose_name_plural = "Controles de notificacao"
        constraints = [
            models.UniqueConstraint(
                fields=["agent", "notification_type"],
                name="uniq_notifthr_agent_type",
            ),
        ]

    def __str__(self):
        return f"{self.agent_id} - {self.notification_type}"


class JobRun(models.Model):
    job_name = models.CharField(
        max_length=80,
        choices=JobNameChoices.choices,
        verbose_name="Nome do job",
    )
    started_at = models.DateTimeField(verbose_name="Inicio")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Fim")
    status = models.CharField(
        max_length=20,
        choices=JobRunStatusChoices.choices,
        verbose_name="Status",
    )
    summary = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name="Resumo",
    )
    error_detail = models.TextField(
        null=True,
        blank=True,
        verbose_name="Detalhes do erro",
    )

    class Meta:
        verbose_name = "Execucao de job"
        verbose_name_plural = "Execucoes de jobs"
        indexes = [
            models.Index(fields=["job_name", "started_at"], name="idx_jobrun_name_start"),
        ]

    def __str__(self):
        return f"{self.job_name} - {self.status} ({self.started_at})"
