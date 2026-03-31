"""
Comando para gerar dados fictícios de monitoramento.

Útil para testes quando o banco legado está indisponível ou para demonstrações.
Usa os agentes existentes no banco e gera eventos/jornadas/stats realistas.

Uso:
    python manage.py generate_mock_data --date 2026-03-27
    python manage.py generate_mock_data --from 2026-03-20 --to 2026-03-27
    python manage.py generate_mock_data --today
    python manage.py generate_mock_data --days 7
"""

import random
from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.monitoring.models import Agent, AgentDayStats, AgentEvent, AgentWorkday
from apps.monitoring.services.day_stats_service import rebuild_agent_day_stats


class Command(BaseCommand):
    help = "Gera dados fictícios realistas para testes"

    PAUSE_TYPES = [
        ("ALMOÇO", 3600, 4500),  # 1h a 1h15
        ("LANCHE", 600, 900),  # 10min a 15min
        ("BANHEIRO", 180, 420),  # 3min a 7min
        ("TREINAMENTO", 1800, 3600),  # 30min a 1h
        ("REUNIÃO", 1800, 5400),  # 30min a 1h30
        ("PAUSA TÉCNICA", 300, 900),  # 5min a 15min
        ("SUPORTE TI", 600, 1800),  # 10min a 30min
    ]

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="Data específica YYYY-MM-DD")
        parser.add_argument("--from", dest="date_from", type=str, help="Data inicial YYYY-MM-DD")
        parser.add_argument("--to", dest="date_to", type=str, help="Data final YYYY-MM-DD")
        parser.add_argument("--today", action="store_true", help="Gerar para hoje")
        parser.add_argument("--days", type=int, help="Últimos N dias")
        parser.add_argument("--agents", type=int, default=None, help="Número de agentes (usa existentes)")
        parser.add_argument("--clear", action="store_true", help="Limpar dados existentes antes")

    def handle(self, *args, **options):
        date_from, date_to = self._resolve_dates(options)
        
        self.stdout.write(f"Gerando dados fictícios de {date_from} até {date_to}")
        
        agents = list(Agent.objects.filter(ativo=True))
        if not agents:
            self.stdout.write(self.style.ERROR("Nenhum agente ativo encontrado. Crie agentes primeiro."))
            return
        
        if options["agents"]:
            agents = random.sample(agents, min(options["agents"], len(agents)))
        
        self.stdout.write(f"Usando {len(agents)} agentes")
        
        if options["clear"]:
            self._clear_data(date_from, date_to)
        
        current_date = date_from
        total_workdays = 0
        total_events = 0
        
        while current_date <= date_to:
            # Pular finais de semana (opcional)
            if current_date.weekday() < 5:  # Segunda a Sexta
                wd, ev = self._generate_day_data(current_date, agents)
                total_workdays += wd
                total_events += ev
            
            current_date += timedelta(days=1)
        
        self.stdout.write(f"\nRecalculando estatísticas...")
        rebuild_agent_day_stats(date_from=date_from, date_to=date_to)
        
        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Dados gerados com sucesso!\n"
            f"  Jornadas: {total_workdays}\n"
            f"  Eventos: {total_events}\n"
            f"  Período: {date_from} até {date_to}"
        ))

    def _resolve_dates(self, options):
        if options["date"]:
            date = datetime.strptime(options["date"], "%Y-%m-%d").date()
            return date, date
        
        if options["date_from"] and options["date_to"]:
            date_from = datetime.strptime(options["date_from"], "%Y-%m-%d").date()
            date_to = datetime.strptime(options["date_to"], "%Y-%m-%d").date()
            return date_from, date_to
        
        if options["days"]:
            date_to = timezone.now().date()
            date_from = date_to - timedelta(days=options["days"] - 1)
            return date_from, date_to
        
        # Default: hoje
        today = timezone.now().date()
        return today, today

    def _clear_data(self, date_from, date_to):
        self.stdout.write("Limpando dados existentes...")
        
        AgentEvent.objects.filter(
            source="MOCK",
            dt_inicio__date__gte=date_from,
            dt_inicio__date__lte=date_to
        ).delete()
        
        AgentWorkday.objects.filter(
            source="MOCK",
            work_date__gte=date_from,
            work_date__lte=date_to
        ).delete()
        
        AgentDayStats.objects.filter(
            agent__in=Agent.objects.filter(ativo=True),
            data_ref__gte=date_from,
            data_ref__lte=date_to
        ).delete()

    @transaction.atomic
    def _generate_day_data(self, work_date, agents):
        workdays_created = 0
        events_created = 0
        
        for agent in agents:
            # 80% de chance de trabalhar neste dia
            if random.random() > 0.2:
                wd, ev = self._generate_agent_day(agent, work_date)
                workdays_created += wd
                events_created += ev
        
        return workdays_created, events_created

    def _generate_agent_day(self, agent, work_date):
        # Horários de trabalho variados
        start_hour = random.choice([7, 8, 9])
        start_minute = random.choice([0, 15, 30, 45])
        end_hour = random.choice([16, 17, 18])
        end_minute = random.choice([0, 15, 30, 45])
        
        dt_inicio = timezone.make_aware(
            datetime.combine(work_date, time(start_hour, start_minute))
        )
        dt_fim = timezone.make_aware(
            datetime.combine(work_date, time(end_hour, end_minute))
        )
        
        total_seconds = int((dt_fim - dt_inicio).total_seconds())
        
        # Criar jornada (get_or_create para evitar violação de UniqueConstraint)
        AgentWorkday.objects.get_or_create(
            source="MOCK",
            cd_operador=agent.cd_operador,
            work_date=work_date,
            defaults={
                "nm_operador": agent.nm_agente or str(agent.cd_operador),
                "ext_event": int(work_date.strftime('%Y%m%d')) * 100000 + agent.cd_operador,
                "dt_inicio": dt_inicio,
                "dt_fim": dt_fim,
                "duracao_seg": total_seconds,
            },
        )
        
        # Gerar pausas realistas
        events_created = self._generate_pauses(agent, dt_inicio, dt_fim)
        
        return 1, events_created

    def _generate_pauses(self, agent, dt_inicio, dt_fim):
        events = []
        current_time = dt_inicio
        
        # Número de pausas (3 a 8 por dia)
        num_pauses = random.randint(3, 8)
        
        work_duration = (dt_fim - dt_inicio).total_seconds()
        available_time = work_duration
        
        for i in range(num_pauses):
            if available_time < 600:  # Menos de 10 min restantes
                break
            
            # Escolher tipo de pausa
            pause_name, min_dur, max_dur = random.choice(self.PAUSE_TYPES)
            effective_max = max(min_dur, min(max_dur, int(available_time * 0.3)))
            duration = random.randint(min_dur, effective_max)
            
            # Tempo aleatório até próxima pausa (30min a 2h)
            gap = random.randint(1800, 7200)
            current_time += timedelta(seconds=gap)
            
            if current_time >= dt_fim:
                break
            
            pause_end = current_time + timedelta(seconds=duration)
            
            if pause_end > dt_fim:
                pause_end = dt_fim
                duration = int((pause_end - current_time).total_seconds())
            
            event = AgentEvent.objects.create(
                source="MOCK",
                cd_operador=agent.cd_operador,
                tp_evento="PAUSA",
                nm_pausa=pause_name,
                dt_inicio=current_time,
                dt_fim=pause_end,
                duracao_seg=duration,
                agent=agent,
                source_event_hash=f"MOCK_{agent.cd_operador}_{current_time.isoformat()}_{pause_name}"
            )
            
            events.append(event)
            current_time = pause_end
            available_time -= (gap + duration)
        
        return len(events)
