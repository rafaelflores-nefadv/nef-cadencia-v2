# Plano de Refatoração por Etapas

**Data:** 18 de Março de 2026  
**Versão:** 1.0  
**Status:** Proposta sem implementação

---

## 1. Visão Geral

### 1.1 Objetivo
Refatorar o projeto Django NEF Cadência v2 de forma **incremental e sem quebrar compatibilidade**, adicionando camadas arquiteturais faltantes e melhorando a organização do código.

### 1.2 Princípios
- ✅ **Sem reescrita do zero** - Evolução gradual
- ✅ **Sem quebra de compatibilidade** - Sistema continua funcionando
- ✅ **Testes antes de refatorar** - Garantir comportamento
- ✅ **Commits pequenos e frequentes** - Fácil rollback
- ✅ **Uma etapa por vez** - Validar antes de prosseguir

### 1.3 Duração Estimada
- **Etapa 1:** 1-2 semanas
- **Etapa 2:** 2-3 semanas
- **Etapa 3:** 2-3 semanas
- **Etapa 4:** 3-4 semanas
- **Etapa 5:** 2-3 semanas
- **Total:** 10-15 semanas (2.5-4 meses)

---

## 2. Etapa 1: Fundação e Estrutura Base

**Duração:** 1-2 semanas  
**Risco:** Baixo  
**Objetivo:** Criar estrutura base sem quebrar nada

### 2.1 Atividades

#### 2.1.1 Criar Arquivos Base (Dia 1)
```bash
# Monitoring
touch apps/monitoring/forms.py
touch apps/monitoring/permissions.py
touch apps/monitoring/selectors.py
touch apps/monitoring/validators.py
touch apps/monitoring/serializers.py

# Rules
touch apps/rules/forms.py
touch apps/rules/permissions.py
touch apps/rules/selectors.py
touch apps/rules/validators.py
touch apps/rules/urls.py
touch apps/rules/views.py

# Messaging
touch apps/messaging/forms.py
touch apps/messaging/permissions.py
touch apps/messaging/selectors.py
touch apps/messaging/urls.py
touch apps/messaging/views.py

# Integrations
touch apps/integrations/forms.py
touch apps/integrations/permissions.py
touch apps/integrations/selectors.py
touch apps/integrations/urls.py
touch apps/integrations/views.py

# Assistant
touch apps/assistant/forms.py
touch apps/assistant/permissions.py
touch apps/assistant/selectors.py

# Accounts
touch apps/accounts/forms.py
touch apps/accounts/permissions.py
```

#### 2.1.2 Criar Estrutura de Testes (Dia 2-3)
```bash
# Monitoring
mkdir -p apps/monitoring/tests/test_services
touch apps/monitoring/tests/__init__.py
touch apps/monitoring/tests/test_models.py
touch apps/monitoring/tests/test_views.py
touch apps/monitoring/tests/test_forms.py
touch apps/monitoring/tests/test_selectors.py
touch apps/monitoring/tests/test_permissions.py

# Copiar testes existentes para nova estrutura
# Manter arquivos antigos por enquanto
```

#### 2.1.3 Adicionar Docstrings Base (Dia 4-5)
```python
# Em cada arquivo novo, adicionar estrutura base

# forms.py
"""
Formulários para validação de entrada do app <nome>.

Este módulo contém formulários Django para:
- Validação de dados de entrada
- Limpeza e normalização
- Mensagens de erro customizadas
"""

# permissions.py
"""
Permissões e controle de acesso do app <nome>.

Este módulo contém classes de permissão para:
- Controle de acesso granular
- Verificações baseadas em roles
- Verificações baseadas em objetos
"""

# selectors.py
"""
Queries reutilizáveis do app <nome>.

Este módulo contém funções para:
- Queries ORM complexas
- Filtros reutilizáveis
- Agregações e anotações
- Otimizações (select_related, prefetch_related)

Convenção: Funções retornam QuerySets ou listas.
"""

# validators.py
"""
Validações de domínio do app <nome>.

Este módulo contém validadores para:
- Regras de negócio
- Validações customizadas
- Validações reutilizáveis em forms e models
"""

# serializers.py
"""
Formatação de dados para saída do app <nome>.

Este módulo contém funções para:
- Transformação de dados para templates
- Formatação consistente
- Preparação de contexto
"""
```

#### 2.1.4 Configurar Imports (Dia 5)
```python
# Em cada __init__.py dos novos módulos
# Facilitar imports futuros

# apps/monitoring/forms.py
from .forms import (
    DashboardFilterForm,
    PauseClassificationForm,
    # ... adicionar conforme implementar
)

__all__ = [
    'DashboardFilterForm',
    'PauseClassificationForm',
]
```

### 2.2 Entregáveis
- ✅ Estrutura de arquivos criada
- ✅ Estrutura de testes criada
- ✅ Docstrings base adicionadas
- ✅ Projeto continua funcionando normalmente
- ✅ Commit: "feat: add base architecture structure"

### 2.3 Validação
```bash
# Verificar que projeto ainda funciona
python manage.py check
python manage.py test
python manage.py runserver
# Acessar dashboards e verificar funcionamento
```

---

## 3. Etapa 2: Extrair Lógica de Queries (Selectors)

**Duração:** 2-3 semanas  
**Risco:** Baixo-Médio  
**Objetivo:** Mover queries ORM para selectors

### 3.1 Atividades

#### 3.1.1 Identificar Queries em Views (Dia 1-2)
```python
# Mapear todas as queries em monitoring/views.py
# Exemplo de queries encontradas:

# Query 1: Agentes ativos
Agent.objects.filter(ativo=True)

# Query 2: Eventos do dia
AgentEvent.objects.filter(
    dt_inicio__gte=period_start,
    dt_inicio__lt=period_end
).select_related('agent')

# Query 3: Estatísticas do dia
AgentDayStats.objects.filter(
    data_ref=selected_date
).select_related('agent')

# ... mapear todas
```

#### 3.1.2 Implementar Selectors Básicos (Dia 3-7)
```python
# apps/monitoring/selectors.py

from django.db.models import QuerySet
from .models import Agent, AgentEvent, AgentDayStats, AgentWorkday

def get_active_agents() -> QuerySet[Agent]:
    """
    Retorna todos os agentes ativos.
    
    Returns:
        QuerySet de Agent filtrado por ativo=True
    """
    return Agent.objects.filter(ativo=True)


def get_events_for_period(
    start_date,
    end_date,
    source: str | None = None,
    agent_ids: list[int] | None = None
) -> QuerySet[AgentEvent]:
    """
    Retorna eventos para um período específico.
    
    Args:
        start_date: Data/hora de início
        end_date: Data/hora de fim
        source: Filtro opcional por fonte
        agent_ids: Filtro opcional por IDs de agentes
    
    Returns:
        QuerySet de AgentEvent com select_related('agent')
    """
    qs = AgentEvent.objects.filter(
        dt_inicio__gte=start_date,
        dt_inicio__lt=end_date
    ).select_related('agent')
    
    if source:
        qs = qs.filter(source=source)
    
    if agent_ids:
        qs = qs.filter(agent_id__in=agent_ids)
    
    return qs


def get_day_stats_for_date(
    date,
    agent_ids: list[int] | None = None
) -> QuerySet[AgentDayStats]:
    """
    Retorna estatísticas diárias para uma data.
    
    Args:
        date: Data de referência
        agent_ids: Filtro opcional por IDs de agentes
    
    Returns:
        QuerySet de AgentDayStats com select_related('agent')
    """
    qs = AgentDayStats.objects.filter(
        data_ref=date
    ).select_related('agent')
    
    if agent_ids:
        qs = qs.filter(agent_id__in=agent_ids)
    
    return qs


def get_workdays_for_date(
    date,
    source: str | None = None
) -> QuerySet[AgentWorkday]:
    """
    Retorna jornadas de trabalho para uma data.
    
    Args:
        date: Data de trabalho
        source: Filtro opcional por fonte
    
    Returns:
        QuerySet de AgentWorkday
    """
    qs = AgentWorkday.objects.filter(work_date=date)
    
    if source:
        qs = qs.filter(source=source)
    
    return qs


def get_pause_events_for_period(
    start_date,
    end_date,
    exclude_pause_names: list[str] | None = None
) -> QuerySet[AgentEvent]:
    """
    Retorna apenas eventos de pausa para um período.
    
    Args:
        start_date: Data/hora de início
        end_date: Data/hora de fim
        exclude_pause_names: Nomes de pausas a excluir
    
    Returns:
        QuerySet de AgentEvent filtrado por pausas
    """
    qs = get_events_for_period(start_date, end_date)
    qs = qs.filter(tp_evento='PAUSA')
    
    if exclude_pause_names:
        qs = qs.exclude(nm_pausa__in=exclude_pause_names)
    
    return qs
```

#### 3.1.3 Adicionar Testes para Selectors (Dia 8-10)
```python
# apps/monitoring/tests/test_selectors.py

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.monitoring.models import Agent, AgentEvent
from apps.monitoring.selectors import (
    get_active_agents,
    get_events_for_period,
)


class GetActiveAgentsTest(TestCase):
    def setUp(self):
        Agent.objects.create(cd_operador=1, ativo=True)
        Agent.objects.create(cd_operador=2, ativo=False)
        Agent.objects.create(cd_operador=3, ativo=True)
    
    def test_returns_only_active_agents(self):
        agents = get_active_agents()
        self.assertEqual(agents.count(), 2)
        self.assertTrue(all(agent.ativo for agent in agents))


class GetEventsForPeriodTest(TestCase):
    def setUp(self):
        self.agent = Agent.objects.create(cd_operador=1, ativo=True)
        self.today = timezone.now().replace(hour=0, minute=0, second=0)
        self.tomorrow = self.today + timedelta(days=1)
        
        # Evento de hoje
        AgentEvent.objects.create(
            agent=self.agent,
            cd_operador=1,
            tp_evento='LOGON',
            dt_inicio=self.today + timedelta(hours=8),
            source='test',
            source_event_hash='hash1'
        )
        
        # Evento de amanhã
        AgentEvent.objects.create(
            agent=self.agent,
            cd_operador=1,
            tp_evento='LOGON',
            dt_inicio=self.tomorrow + timedelta(hours=8),
            source='test',
            source_event_hash='hash2'
        )
    
    def test_filters_by_period(self):
        events = get_events_for_period(self.today, self.tomorrow)
        self.assertEqual(events.count(), 1)
    
    def test_filters_by_source(self):
        events = get_events_for_period(
            self.today,
            self.tomorrow + timedelta(days=1),
            source='test'
        )
        self.assertEqual(events.count(), 2)
```

#### 3.1.4 Refatorar Views para Usar Selectors (Dia 11-14)
```python
# apps/monitoring/views.py (ou views/dashboard_views.py)

# ANTES
class DashboardView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        # ...
        active_agents_qs = Agent.objects.filter(ativo=True)
        events_day_qs = AgentEvent.objects.filter(
            dt_inicio__gte=period_start,
            dt_inicio__lt=period_end
        ).select_related('agent')
        # ...

# DEPOIS
from .selectors import get_active_agents, get_events_for_period

class DashboardView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        # ...
        active_agents_qs = get_active_agents()
        events_day_qs = get_events_for_period(period_start, period_end)
        # ...
```

### 3.2 Entregáveis
- ✅ Selectors implementados para queries principais
- ✅ Testes unitários para selectors
- ✅ Views refatoradas para usar selectors
- ✅ Documentação inline (docstrings)
- ✅ Commit: "refactor: extract queries to selectors"

### 3.3 Validação
```bash
# Rodar testes
python manage.py test apps.monitoring.tests.test_selectors

# Verificar dashboards funcionam igual
python manage.py runserver
# Comparar resultados antes/depois
```

---

## 4. Etapa 3: Extrair Lógica de Negócio (Services)

**Duração:** 2-3 semanas  
**Risco:** Médio  
**Objetivo:** Mover cálculos e lógica de negócio para services

### 4.1 Atividades

#### 4.1.1 Criar Services de Métricas (Dia 1-5)
```python
# apps/monitoring/services/metrics_service.py

from typing import Dict, List
from django.db.models import QuerySet

def calculate_operator_metrics(
    events_qs: QuerySet,
    workday_qs: QuerySet,
    stats_qs: QuerySet,
    pause_classifications: Dict
) -> List[Dict]:
    """
    Calcula métricas agregadas por operador.
    
    Args:
        events_qs: QuerySet de eventos
        workday_qs: QuerySet de jornadas
        stats_qs: QuerySet de estatísticas
        pause_classifications: Dicionário de classificações
    
    Returns:
        Lista de dicionários com métricas por operador
    """
    # Lógica extraída de DashboardView._build_operator_metrics
    operator_metrics = {}
    
    # Processar eventos
    for event in events_qs:
        cd_op = event.cd_operador
        if cd_op not in operator_metrics:
            operator_metrics[cd_op] = {
                'cd_operador': cd_op,
                'nm_agente': event.agent.nm_agente if event.agent else None,
                'qtd_pausas': 0,
                'tempo_pausas_seg': 0,
                'tempo_produtivo_seg': 0,
                # ... outros campos
            }
        
        # Calcular métricas
        if event.tp_evento == 'PAUSA':
            operator_metrics[cd_op]['qtd_pausas'] += 1
            operator_metrics[cd_op]['tempo_pausas_seg'] += event.duracao_seg or 0
    
    # Processar workdays
    for workday in workday_qs:
        cd_op = workday.cd_operador
        if cd_op in operator_metrics:
            operator_metrics[cd_op]['tempo_total_seg'] = workday.duracao_seg
    
    # Calcular tempo produtivo
    for cd_op, metrics in operator_metrics.items():
        total = metrics.get('tempo_total_seg', 0)
        pausas = metrics.get('tempo_pausas_seg', 0)
        metrics['tempo_produtivo_seg'] = max(0, total - pausas)
    
    return list(operator_metrics.values())


def calculate_operational_score(
    taxa_ocupacao_pct: float,
    alert_totals: Dict[str, int]
) -> int:
    """
    Calcula score operacional baseado em ocupação e alertas.
    
    Args:
        taxa_ocupacao_pct: Taxa de ocupação em percentual
        alert_totals: Dicionário com contagem de alertas por severidade
    
    Returns:
        Score operacional (0-100)
    """
    base_score = int(round(max(0.0, min(float(taxa_ocupacao_pct or 0.0), 100.0))))
    crit_penalty = min(int(alert_totals.get("crit", 0)) * 8, 40)
    warn_penalty = min(int(alert_totals.get("warn", 0)) * 3, 24)
    info_penalty = min(int(alert_totals.get("info", 0)), 8)
    return max(0, base_score - crit_penalty - warn_penalty - info_penalty)


def calculate_health_score(
    produtividade_score: float,
    risco_score: float,
    ocupacao_score: float,
    pipeline_score: float,
) -> int:
    """
    Calcula score de saúde geral do sistema.
    
    Args:
        produtividade_score: Score de produtividade
        risco_score: Score de risco
        ocupacao_score: Score de ocupação
        pipeline_score: Score de pipeline
    
    Returns:
        Score de saúde (0-100)
    """
    weighted = (
        (float(produtividade_score or 0.0) * 0.35)
        + (float(risco_score or 0.0) * 0.25)
        + (float(ocupacao_score or 0.0) * 0.20)
        + (float(pipeline_score or 0.0) * 0.20)
    )
    return max(0, min(int(round(weighted)), 100))
```

#### 4.1.2 Criar Services de Alertas (Dia 6-8)
```python
# apps/monitoring/services/alerts_service.py

from typing import List, Dict
from django.db.models import QuerySet

def build_operational_alerts(
    operator_metrics: List[Dict],
    no_activity_agents: List[Dict],
    events_day_qs: QuerySet,
    events_by_hour: List[Dict],
    total_events_day: int,
    pause_category_totals: Dict,
    pause_category_counts: Dict,
    config: Dict
) -> List[Dict]:
    """
    Gera alertas operacionais baseados em métricas.
    
    Args:
        operator_metrics: Métricas por operador
        no_activity_agents: Agentes sem atividade
        events_day_qs: QuerySet de eventos do dia
        events_by_hour: Eventos agrupados por hora
        total_events_day: Total de eventos
        pause_category_totals: Totais por categoria
        pause_category_counts: Contagens por categoria
        config: Configuração de thresholds
    
    Returns:
        Lista de alertas com severidade e mensagem
    """
    alerts = []
    
    # Alerta: Agentes sem atividade
    if no_activity_agents:
        alerts.append({
            'severity': 'warn',
            'title': 'Agentes sem atividade',
            'message': f'{len(no_activity_agents)} agentes ativos sem eventos registrados',
            'count': len(no_activity_agents),
            'agents': no_activity_agents[:5],  # Top 5
        })
    
    # Alerta: Pausas excessivas
    high_pause_agents = [
        m for m in operator_metrics
        if m.get('tempo_pausas_seg', 0) > config.get('high_pause_threshold_seg', 3600)
    ]
    if high_pause_agents:
        alerts.append({
            'severity': 'crit',
            'title': 'Pausas excessivas',
            'message': f'{len(high_pause_agents)} agentes com pausas acima do limite',
            'count': len(high_pause_agents),
        })
    
    # Alerta: Baixa ocupação
    low_occupancy_agents = [
        m for m in operator_metrics
        if m.get('taxa_ocupacao_pct', 0) < config.get('low_occupancy_threshold_pct', 70)
    ]
    if low_occupancy_agents:
        alerts.append({
            'severity': 'warn',
            'title': 'Baixa ocupação',
            'message': f'{len(low_occupancy_agents)} agentes com ocupação abaixo de 70%',
            'count': len(low_occupancy_agents),
        })
    
    # Alerta: Gaps de eventos
    # ... lógica de detecção de gaps
    
    return alerts
```

#### 4.1.3 Criar Services de Rankings (Dia 9-11)
```python
# apps/monitoring/services/ranking_service.py

from typing import List, Dict

def build_pause_rankings(
    operator_metrics: List[Dict]
) -> tuple[List[Dict], List[Dict]]:
    """
    Gera rankings de pausas por tempo e quantidade.
    
    Args:
        operator_metrics: Métricas por operador
    
    Returns:
        Tupla com (ranking_por_tempo, ranking_por_quantidade)
    """
    # Ranking por tempo de pausas
    by_time = sorted(
        operator_metrics,
        key=lambda x: x.get('tempo_pausas_seg', 0),
        reverse=True
    )[:10]
    
    # Ranking por quantidade de pausas
    by_count = sorted(
        operator_metrics,
        key=lambda x: x.get('qtd_pausas', 0),
        reverse=True
    )[:10]
    
    return by_time, by_count


def build_productivity_ranking(
    operator_metrics: List[Dict]
) -> List[Dict]:
    """
    Gera ranking de produtividade.
    
    Args:
        operator_metrics: Métricas por operador
    
    Returns:
        Lista ordenada por tempo produtivo
    """
    ranking = sorted(
        operator_metrics,
        key=lambda x: x.get('tempo_produtivo_seg', 0),
        reverse=True
    )[:10]
    
    return ranking


def build_gamified_leaderboard(
    leaderboard_agents: List[Dict],
    operation_average: float
) -> List[Dict]:
    """
    Adiciona gamificação ao leaderboard.
    
    Args:
        leaderboard_agents: Agentes do leaderboard
        operation_average: Média da operação
    
    Returns:
        Leaderboard com medalhas e badges
    """
    medals = {
        1: {"name": "Ouro", "emoji": "🥇"},
        2: {"name": "Prata", "emoji": "🥈"},
        3: {"name": "Bronze", "emoji": "🥉"},
    }
    
    for idx, agent in enumerate(leaderboard_agents, start=1):
        agent['position'] = idx
        agent['medal'] = medals.get(idx)
        
        # Badges
        agent['badges'] = []
        if agent.get('tempo_produtivo_seg', 0) > operation_average * 1.2:
            agent['badges'].append('⭐ Destaque')
        if agent.get('qtd_pausas', 0) < operation_average * 0.5:
            agent['badges'].append('🎯 Focado')
    
    return leaderboard_agents
```

#### 4.1.4 Adicionar Testes para Services (Dia 12-14)
```python
# apps/monitoring/tests/test_services/test_metrics_service.py

from django.test import TestCase
from apps.monitoring.services.metrics_service import (
    calculate_operational_score,
    calculate_health_score,
)


class CalculateOperationalScoreTest(TestCase):
    def test_perfect_score(self):
        score = calculate_operational_score(
            taxa_ocupacao_pct=100.0,
            alert_totals={'crit': 0, 'warn': 0, 'info': 0}
        )
        self.assertEqual(score, 100)
    
    def test_score_with_critical_alerts(self):
        score = calculate_operational_score(
            taxa_ocupacao_pct=100.0,
            alert_totals={'crit': 3, 'warn': 0, 'info': 0}
        )
        self.assertEqual(score, 76)  # 100 - (3 * 8)
    
    def test_score_with_low_occupancy(self):
        score = calculate_operational_score(
            taxa_ocupacao_pct=50.0,
            alert_totals={'crit': 0, 'warn': 0, 'info': 0}
        )
        self.assertEqual(score, 50)
```

#### 4.1.5 Refatorar Views para Usar Services (Dia 15)
```python
# apps/monitoring/views/dashboard_views.py

from ..selectors import get_active_agents, get_events_for_period
from ..services.metrics_service import (
    calculate_operator_metrics,
    calculate_operational_score,
    calculate_health_score,
)
from ..services.alerts_service import build_operational_alerts
from ..services.ranking_service import (
    build_pause_rankings,
    build_productivity_ranking,
    build_gamified_leaderboard,
)

class DashboardView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Queries (via selectors)
        active_agents_qs = get_active_agents()
        events_day_qs = get_events_for_period(period_start, period_end)
        # ...
        
        # Cálculos (via services)
        operator_metrics = calculate_operator_metrics(
            events_qs=events_day_qs,
            workday_qs=workday_day_qs,
            stats_qs=stats_qs,
            pause_classifications=pause_classifications,
        )
        
        alerts = build_operational_alerts(
            operator_metrics=operator_metrics,
            no_activity_agents=no_activity_agents,
            # ...
        )
        
        top_pause_time, top_pause_count = build_pause_rankings(operator_metrics)
        top_productivity = build_productivity_ranking(operator_metrics)
        leaderboard = build_gamified_leaderboard(top_productivity[:10], avg)
        
        score_operacional = calculate_operational_score(
            taxa_ocupacao_pct=taxa_ocupacao_pct,
            alert_totals=alert_totals,
        )
        
        health_score = calculate_health_score(
            produtividade_score=prod_score,
            risco_score=risk_score,
            ocupacao_score=ocup_score,
            pipeline_score=pipe_score,
        )
        
        # Preparar contexto
        context.update({
            'operator_metrics': operator_metrics,
            'alerts': alerts,
            'top_pause_time': top_pause_time,
            'top_productivity': top_productivity,
            'leaderboard': leaderboard,
            'score_operacional': score_operacional,
            'health_score': health_score,
            # ...
        })
        
        return context
```

### 4.2 Entregáveis
- ✅ Services de métricas implementados
- ✅ Services de alertas implementados
- ✅ Services de rankings implementados
- ✅ Testes unitários para services
- ✅ Views refatoradas (muito mais simples!)
- ✅ Commit: "refactor: extract business logic to services"

### 4.3 Validação
```bash
# Rodar testes
python manage.py test apps.monitoring.tests.test_services

# Comparar resultados dos dashboards
# Antes e depois devem ser idênticos
```

---

## 5. Etapa 4: Adicionar Forms, Validators e Permissions

**Duração:** 3-4 semanas  
**Risco:** Baixo-Médio  
**Objetivo:** Adicionar camadas de validação e controle de acesso

### 5.1 Atividades

#### 5.1.1 Implementar Forms (Dia 1-7)
```python
# apps/monitoring/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Agent, PauseClassification
from .validators import validate_operator_code, validate_date_range


class DashboardFilterForm(forms.Form):
    """Formulário de filtros do dashboard."""
    
    data_ref = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Data de Referência'
    )
    
    period_type = forms.ChoiceField(
        required=False,
        choices=[
            ('day', 'Dia'),
            ('week', 'Semana'),
            ('month', 'Mês'),
        ],
        label='Tipo de Período'
    )
    
    source = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas')] + [
            ('legacy', 'Legacy'),
            ('lh', 'LH'),
        ],
        label='Fonte'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        # Validações customizadas
        return cleaned_data


class AgentForm(forms.ModelForm):
    """Formulário de cadastro/edição de agente."""
    
    class Meta:
        model = Agent
        fields = [
            'cd_operador',
            'nm_agente',
            'nm_agente_code',
            'nr_ramal',
            'email',
            'ativo',
        ]
        widgets = {
            'cd_operador': forms.NumberInput(attrs={'min': 1}),
            'email': forms.EmailInput(),
        }
    
    def clean_cd_operador(self):
        cd_operador = self.cleaned_data['cd_operador']
        validate_operator_code(cd_operador)
        
        # Verificar duplicação
        if Agent.objects.filter(cd_operador=cd_operador).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Código de operador já existe')
        
        return cd_operador


class PauseClassificationForm(forms.ModelForm):
    """Formulário de classificação de pausas."""
    
    class Meta:
        model = PauseClassification
        fields = ['source', 'pause_name', 'category', 'is_active']
    
    def clean_pause_name(self):
        pause_name = self.cleaned_data['pause_name']
        if not pause_name.strip():
            raise ValidationError('Nome da pausa não pode ser vazio')
        return pause_name.strip()
```

#### 5.1.2 Implementar Validators (Dia 8-10)
```python
# apps/monitoring/validators.py

from django.core.exceptions import ValidationError
from datetime import date, timedelta


def validate_operator_code(value: int):
    """Valida código de operador."""
    if value <= 0:
        raise ValidationError('Código de operador deve ser positivo')
    if value > 999999:
        raise ValidationError('Código de operador muito grande')


def validate_date_range(start_date: date, end_date: date, max_days: int = 31):
    """Valida range de datas."""
    if start_date > end_date:
        raise ValidationError('Data inicial deve ser menor ou igual à data final')
    
    delta = (end_date - start_date).days
    if delta > max_days:
        raise ValidationError(f'Período não pode exceder {max_days} dias')


def validate_pause_name(value: str):
    """Valida nome de pausa."""
    if not value or not value.strip():
        raise ValidationError('Nome da pausa não pode ser vazio')
    
    if len(value.strip()) < 2:
        raise ValidationError('Nome da pausa deve ter pelo menos 2 caracteres')


def validate_email_or_ramal(email: str | None, ramal: str | None):
    """Valida que pelo menos email ou ramal está preenchido."""
    if not email and not ramal:
        raise ValidationError('Informe pelo menos email ou ramal')
```

#### 5.1.3 Implementar Permissions (Dia 11-14)
```python
# apps/monitoring/permissions.py

from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)


class CanViewDashboard(LoginRequiredMixin):
    """Permissão para visualizar dashboards."""
    pass  # Todos os usuários logados podem ver


class CanManageAgents(PermissionRequiredMixin):
    """Permissão para gerenciar agentes."""
    permission_required = 'monitoring.change_agent'
    
    def handle_no_permission(self):
        messages.error(self.request, 'Você não tem permissão para gerenciar agentes')
        return redirect('dashboard')


class CanRebuildStats(UserPassesTestMixin):
    """Permissão para rebuild de estatísticas."""
    
    def test_func(self):
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        messages.error(self.request, 'Apenas administradores podem rebuild estatísticas')
        return redirect('dashboard')


class CanManagePauseClassification(UserPassesTestMixin):
    """Permissão para gerenciar classificação de pausas."""
    
    def test_func(self):
        return self.request.user.is_staff or \
               self.request.user.has_perm('monitoring.change_pauseclassification')


# Decorators para function-based views
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def require_staff(view_func):
    """Decorator que requer usuário staff."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Acesso negado')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
```

#### 5.1.4 Aplicar em Views (Dia 15-18)
```python
# apps/monitoring/views/dashboard_views.py

from ..permissions import CanViewDashboard, CanRebuildStats

class DashboardView(CanViewDashboard, TemplateView):
    template_name = "monitoring/dashboard_executive.html"
    # ...


class DashboardRebuildStatsView(CanRebuildStats, View):
    def post(self, request):
        # ...
        pass


# apps/monitoring/views/agent_views.py

from ..permissions import CanViewDashboard, CanManageAgents
from ..forms import AgentForm

class AgentListView(CanViewDashboard, ListView):
    model = Agent
    template_name = "monitoring/agents_list.html"
    # ...


class AgentCreateView(CanManageAgents, CreateView):
    model = Agent
    form_class = AgentForm
    template_name = "monitoring/agent_form.html"
    success_url = reverse_lazy('agents-list')


class AgentUpdateView(CanManageAgents, UpdateView):
    model = Agent
    form_class = AgentForm
    template_name = "monitoring/agent_form.html"
    success_url = reverse_lazy('agents-list')
```

#### 5.1.5 Adicionar Testes (Dia 19-21)
```python
# apps/monitoring/tests/test_forms.py

from django.test import TestCase
from apps.monitoring.forms import AgentForm, DashboardFilterForm


class AgentFormTest(TestCase):
    def test_valid_form(self):
        form = AgentForm(data={
            'cd_operador': 123,
            'nm_agente': 'João Silva',
            'email': 'joao@example.com',
            'ativo': True,
        })
        self.assertTrue(form.is_valid())
    
    def test_invalid_operator_code(self):
        form = AgentForm(data={
            'cd_operador': -1,
            'nm_agente': 'João Silva',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('cd_operador', form.errors)


# apps/monitoring/tests/test_permissions.py

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from apps.monitoring.permissions import CanRebuildStats


class CanRebuildStatsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.staff_user = User.objects.create_user(
            username='staff',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            is_staff=False
        )
    
    def test_staff_can_rebuild(self):
        request = self.factory.get('/rebuild')
        request.user = self.staff_user
        
        permission = CanRebuildStats()
        permission.request = request
        
        self.assertTrue(permission.test_func())
    
    def test_regular_user_cannot_rebuild(self):
        request = self.factory.get('/rebuild')
        request.user = self.regular_user
        
        permission = CanRebuildStats()
        permission.request = request
        
        self.assertFalse(permission.test_func())
```

### 5.2 Entregáveis
- ✅ Forms implementados
- ✅ Validators implementados
- ✅ Permissions implementadas
- ✅ Views usando forms e permissions
- ✅ Testes para forms, validators e permissions
- ✅ Commit: "feat: add forms, validators and permissions"

---

## 6. Etapa 5: Criar Telas para Substituir Admin

**Duração:** 2-3 semanas  
**Risco:** Baixo  
**Objetivo:** Criar interfaces web para funcionalidades que estão apenas no admin

### 6.1 Priorização

**Alta Prioridade:**
1. Configurações do Sistema (`rules`)
2. Templates de Mensagens (`messaging`)
3. Gestão de Agentes (`monitoring`)

**Média Prioridade:**
4. Integrações (`integrations`)
5. Dashboard de Notificações (`monitoring`)

### 6.2 Atividades

#### 6.2.1 Tela de Configurações (Dia 1-5)
```python
# apps/rules/urls.py

from django.urls import path
from .views import ConfigListView, ConfigEditView

urlpatterns = [
    path('configuracoes', ConfigListView.as_view(), name='config-list'),
    path('configuracoes/<str:key>/editar', ConfigEditView.as_view(), name='config-edit'),
]


# apps/rules/views.py

from django.views.generic import ListView, UpdateView
from django.contrib import messages
from .models import SystemConfig
from .forms import SystemConfigForm
from .permissions import CanManageConfigs


class ConfigListView(CanManageConfigs, ListView):
    model = SystemConfig
    template_name = 'rules/config_list.html'
    context_object_name = 'configs'
    paginate_by = 50
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Agrupar por prefixo
        grouped = {}
        for config in qs:
            prefix = config.config_key.split('.')[0] if '.' in config.config_key else 'geral'
            if prefix not in grouped:
                grouped[prefix] = []
            grouped[prefix].append(config)
        
        self.grouped_configs = grouped
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grouped_configs'] = getattr(self, 'grouped_configs', {})
        return context


class ConfigEditView(CanManageConfigs, UpdateView):
    model = SystemConfig
    form_class = SystemConfigForm
    template_name = 'rules/config_edit.html'
    slug_field = 'config_key'
    slug_url_kwarg = 'key'
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Configuração "{form.instance.config_key}" atualizada')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('config-list')
```

```html
<!-- apps/rules/templates/rules/config_list.html -->

{% extends "layouts/base.html" %}

{% block title %}Configurações do Sistema{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold">Configurações do Sistema</h1>
    </div>
    
    {% for category, configs in grouped_configs.items %}
    <div class="mb-8">
        <h2 class="text-xl font-semibold mb-4 capitalize">{{ category }}</h2>
        <div class="bg-white shadow rounded-lg overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Chave</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Valor</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Atualizado</th>
                        <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Ações</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    {% for config in configs %}
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {{ config.config_key }}
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-500">
                            <code class="bg-gray-100 px-2 py-1 rounded">{{ config.config_value|truncatechars:50 }}</code>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                                {{ config.get_value_type_display }}
                            </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {{ config.updated_at|date:"d/m/Y H:i" }}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <a href="{% url 'config-edit' config.config_key %}" 
                               class="text-indigo-600 hover:text-indigo-900">
                                Editar
                            </a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
```

#### 6.2.2 Tela de Templates de Mensagens (Dia 6-10)
```python
# apps/messaging/urls.py

from django.urls import path
from .views import (
    TemplateListView,
    TemplateCreateView,
    TemplateUpdateView,
    TemplatePreviewView,
)

urlpatterns = [
    path('mensagens', TemplateListView.as_view(), name='template-list'),
    path('mensagens/novo', TemplateCreateView.as_view(), name='template-create'),
    path('mensagens/<int:pk>', TemplateUpdateView.as_view(), name='template-edit'),
    path('mensagens/<int:pk>/preview', TemplatePreviewView.as_view(), name='template-preview'),
]


# apps/messaging/views.py

class TemplateListView(CanManageTemplates, ListView):
    model = MessageTemplate
    template_name = 'messaging/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filtros
        template_type = self.request.GET.get('type')
        if template_type:
            qs = qs.filter(template_type=template_type)
        
        channel = self.request.GET.get('channel')
        if channel:
            qs = qs.filter(channel=channel)
        
        active = self.request.GET.get('active')
        if active == '1':
            qs = qs.filter(active=True)
        elif active == '0':
            qs = qs.filter(active=False)
        
        return qs.order_by('-updated_at')


class TemplatePreviewView(CanManageTemplates, DetailView):
    model = MessageTemplate
    template_name = 'messaging/template_preview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Contexto de exemplo para preview
        sample_context = {
            'nome_agente': 'João Silva',
            'cd_operador': '12345',
            'tempo_pausa': '45 minutos',
            'data': '18/03/2026',
        }
        
        # Renderizar template
        from django.template import Template, Context
        template = Template(self.object.body)
        rendered = template.render(Context(sample_context))
        
        context['rendered_body'] = rendered
        context['sample_context'] = sample_context
        return context
```

#### 6.2.3 Tela de Gestão de Agentes (Dia 11-15)
```python
# apps/monitoring/urls.py (adicionar)

urlpatterns = [
    # ... rotas existentes
    path('agentes/novo', AgentCreateView.as_view(), name='agent-create'),
    path('agentes/<int:pk>/editar', AgentUpdateView.as_view(), name='agent-edit'),
    path('agentes/<int:pk>/desativar', AgentDeactivateView.as_view(), name='agent-deactivate'),
]


# apps/monitoring/views/agent_views.py

class AgentCreateView(CanManageAgents, CreateView):
    model = Agent
    form_class = AgentForm
    template_name = 'monitoring/agent_form.html'
    success_url = reverse_lazy('agents-list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Agente {form.instance.cd_operador} criado com sucesso')
        return super().form_valid(form)


class AgentUpdateView(CanManageAgents, UpdateView):
    model = Agent
    form_class = AgentForm
    template_name = 'monitoring/agent_form.html'
    success_url = reverse_lazy('agents-list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Agente {form.instance.cd_operador} atualizado')
        return super().form_valid(form)


class AgentDeactivateView(CanManageAgents, View):
    def post(self, request, pk):
        agent = get_object_or_404(Agent, pk=pk)
        agent.ativo = False
        agent.save()
        messages.success(request, f'Agente {agent.cd_operador} desativado')
        return redirect('agents-list')
```

```html
<!-- apps/monitoring/templates/monitoring/agent_form.html -->

{% extends "layouts/base.html" %}

{% block title %}{% if object %}Editar{% else %}Novo{% endif %} Agente{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8 max-w-2xl">
    <h1 class="text-3xl font-bold mb-6">
        {% if object %}Editar Agente{% else %}Novo Agente{% endif %}
    </h1>
    
    <form method="post" class="bg-white shadow rounded-lg p-6">
        {% csrf_token %}
        
        {% if form.non_field_errors %}
        <div class="mb-4 p-4 bg-red-50 border border-red-200 rounded">
            {{ form.non_field_errors }}
        </div>
        {% endif %}
        
        <div class="space-y-4">
            {% for field in form %}
            <div>
                <label for="{{ field.id_for_label }}" class="block text-sm font-medium text-gray-700 mb-1">
                    {{ field.label }}
                    {% if field.field.required %}<span class="text-red-500">*</span>{% endif %}
                </label>
                {{ field }}
                {% if field.errors %}
                <p class="mt-1 text-sm text-red-600">{{ field.errors.0 }}</p>
                {% endif %}
                {% if field.help_text %}
                <p class="mt-1 text-sm text-gray-500">{{ field.help_text }}</p>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        
        <div class="mt-6 flex justify-end space-x-3">
            <a href="{% url 'agents-list' %}" 
               class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
                Cancelar
            </a>
            <button type="submit" 
                    class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                Salvar
            </button>
        </div>
    </form>
</div>
{% endblock %}
```

### 6.3 Entregáveis
- ✅ Tela de configurações implementada
- ✅ Tela de templates de mensagens implementada
- ✅ Tela de gestão de agentes implementada
- ✅ Rotas adicionadas ao `urls.py` principal
- ✅ Navegação atualizada
- ✅ Commit: "feat: add web interfaces to replace admin"

---

## 7. Cronograma Consolidado

| Etapa | Atividade | Semanas | Risco |
|-------|-----------|---------|-------|
| 1 | Fundação e Estrutura Base | 1-2 | Baixo |
| 2 | Extrair Lógica de Queries (Selectors) | 2-3 | Baixo-Médio |
| 3 | Extrair Lógica de Negócio (Services) | 2-3 | Médio |
| 4 | Adicionar Forms, Validators e Permissions | 3-4 | Baixo-Médio |
| 5 | Criar Telas para Substituir Admin | 2-3 | Baixo |
| **Total** | | **10-15** | |

---

## 8. Estratégia de Rollout

### 8.1 Por Etapa
1. Desenvolver em branch separada
2. Code review
3. Merge para develop
4. Testes em ambiente de staging
5. Deploy para produção
6. Monitorar por 1-2 dias
7. Prosseguir para próxima etapa

### 8.2 Feature Flags
```python
# settings.py
FEATURE_FLAGS = {
    'use_new_selectors': env.bool('FF_NEW_SELECTORS', default=False),
    'use_new_services': env.bool('FF_NEW_SERVICES', default=False),
    'show_config_page': env.bool('FF_CONFIG_PAGE', default=False),
}

# Em views
if settings.FEATURE_FLAGS['use_new_selectors']:
    agents = get_active_agents()  # Novo
else:
    agents = Agent.objects.filter(ativo=True)  # Antigo
```

### 8.3 Rollback Plan
- Migrations reversíveis
- Feature flags para desabilitar novas features
- Backup de banco antes de cada deploy
- Monitoramento de erros (Sentry)

---

## 9. Métricas de Sucesso

### 9.1 Código
- ✅ `monitoring/views.py` reduzido de 2368 para < 500 linhas
- ✅ Cobertura de testes > 80%
- ✅ Complexidade ciclomática < 10 por função
- ✅ Duplicação de código < 5%

### 9.2 Performance
- ✅ Tempo de resposta dos dashboards mantido ou melhorado
- ✅ Número de queries mantido ou reduzido
- ✅ Uso de memória mantido ou reduzido

### 9.3 Manutenibilidade
- ✅ Tempo para adicionar nova feature reduzido em 30%
- ✅ Tempo para fix de bugs reduzido em 40%
- ✅ Onboarding de novos devs reduzido em 50%

### 9.4 UX
- ✅ Configurações acessíveis sem admin
- ✅ Templates de mensagens editáveis visualmente
- ✅ Gestão de agentes simplificada

---

## 10. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Quebrar funcionalidade existente | Média | Alto | Testes antes/depois, rollback plan |
| Performance degradada | Baixa | Médio | Profiling, otimização de queries |
| Resistência da equipe | Baixa | Baixo | Treinamento, documentação |
| Prazo estourado | Média | Médio | Buffer de 20%, priorização |
| Bugs em produção | Média | Alto | Staging, feature flags, monitoramento |

---

## 11. Próximos Passos Imediatos

1. ✅ Revisar e aprovar este plano
2. ✅ Criar branch `refactor/architecture`
3. ✅ Iniciar Etapa 1 (Fundação)
4. ✅ Setup de ambiente de testes
5. ✅ Configurar CI/CD para rodar testes
6. ✅ Configurar feature flags
7. ✅ Comunicar plano para equipe

---

**Documento gerado automaticamente pela análise técnica do projeto.**  
**Nenhuma alteração foi feita no código durante esta análise.**
