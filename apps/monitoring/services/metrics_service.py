"""
Service para cálculo de métricas operacionais.

Este service extrai a lógica de negócio de cálculo de métricas das views,
tornando o código mais testável e reutilizável.
"""
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
        pause_classifications: Dicionário de classificações de pausas
    
    Returns:
        Lista de dicionários com métricas por operador
    """
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
                'tempo_total_seg': 0,
                'eventos': [],
            }
        
        # Adicionar evento
        operator_metrics[cd_op]['eventos'].append(event)
        
        # Calcular métricas de pausas
        if event.tp_evento == 'PAUSA' and event.duracao_seg:
            operator_metrics[cd_op]['qtd_pausas'] += 1
            operator_metrics[cd_op]['tempo_pausas_seg'] += event.duracao_seg
    
    # Processar workdays (jornadas)
    for workday in workday_qs:
        cd_op = workday.cd_operador
        if cd_op in operator_metrics:
            operator_metrics[cd_op]['tempo_total_seg'] = workday.duracao_seg
    
    # Calcular tempo produtivo
    for cd_op, metrics in operator_metrics.items():
        total = metrics.get('tempo_total_seg', 0)
        pausas = metrics.get('tempo_pausas_seg', 0)
        metrics['tempo_produtivo_seg'] = max(0, total - pausas)
        
        # Calcular taxa de ocupação
        if total > 0:
            metrics['taxa_ocupacao_pct'] = round((metrics['tempo_produtivo_seg'] / total) * 100, 2)
        else:
            metrics['taxa_ocupacao_pct'] = 0.0
    
    return list(operator_metrics.values())


def calculate_operational_score(taxa_ocupacao_pct: float, alert_totals: Dict[str, int]) -> int:
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
        produtividade_score: Score de produtividade (0-100)
        risco_score: Score de risco (0-100)
        ocupacao_score: Score de ocupação (0-100)
        pipeline_score: Score de pipeline (0-100)
    
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


def calculate_pause_distribution(operator_metrics: List[Dict], pause_classifications: Dict) -> Dict:
    """
    Calcula distribuição de pausas por categoria.
    
    Args:
        operator_metrics: Lista de métricas por operador
        pause_classifications: Dicionário de classificações
    
    Returns:
        Dicionário com totais por categoria
    """
    distribution = {
        'LEGAL': {'tempo_seg': 0, 'count': 0},
        'NEUTRAL': {'tempo_seg': 0, 'count': 0},
        'HARMFUL': {'tempo_seg': 0, 'count': 0},
        'UNCLASSIFIED': {'tempo_seg': 0, 'count': 0},
    }
    
    for metrics in operator_metrics:
        for event in metrics.get('eventos', []):
            if event.tp_evento == 'PAUSA':
                # Classificar pausa
                pause_name = event.nm_pausa or ''
                category = pause_classifications.get(pause_name, 'UNCLASSIFIED')
                
                # Adicionar aos totais
                if category in distribution:
                    distribution[category]['tempo_seg'] += event.duracao_seg or 0
                    distribution[category]['count'] += 1
    
    return distribution
