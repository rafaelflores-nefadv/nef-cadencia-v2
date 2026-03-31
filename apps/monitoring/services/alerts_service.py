"""
Service para geração de alertas operacionais.

Este service contém a lógica de detecção e geração de alertas
baseados em métricas operacionais.
"""
from typing import List, Dict
from django.db.models import QuerySet


def build_operational_alerts(
    operator_metrics: List[Dict],
    no_activity_agents: List[Dict],
    config: Dict
) -> List[Dict]:
    """
    Gera alertas operacionais baseados em métricas.
    
    Args:
        operator_metrics: Métricas por operador
        no_activity_agents: Agentes sem atividade
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
            'type': 'no_activity',
        })
    
    # Alerta: Pausas excessivas
    high_pause_threshold = config.get('high_pause_threshold_seg', 3600)
    high_pause_agents = [
        m for m in operator_metrics
        if m.get('tempo_pausas_seg', 0) > high_pause_threshold
    ]
    if high_pause_agents:
        alerts.append({
            'severity': 'crit',
            'title': 'Pausas excessivas',
            'message': f'{len(high_pause_agents)} agentes com pausas acima do limite',
            'count': len(high_pause_agents),
            'threshold': high_pause_threshold,
            'type': 'high_pauses',
        })
    
    # Alerta: Baixa ocupação
    low_occupancy_threshold = config.get('low_occupancy_threshold_pct', 70)
    low_occupancy_agents = [
        m for m in operator_metrics
        if m.get('taxa_ocupacao_pct', 0) < low_occupancy_threshold
    ]
    if low_occupancy_agents:
        alerts.append({
            'severity': 'warn',
            'title': 'Baixa ocupação',
            'message': f'{len(low_occupancy_agents)} agentes com ocupação abaixo de {low_occupancy_threshold}%',
            'count': len(low_occupancy_agents),
            'threshold': low_occupancy_threshold,
            'type': 'low_occupancy',
        })
    
    # Alerta: Alta quantidade de pausas
    high_pause_count_threshold = config.get('high_pause_count_threshold', 20)
    high_pause_count_agents = [
        m for m in operator_metrics
        if m.get('qtd_pausas', 0) > high_pause_count_threshold
    ]
    if high_pause_count_agents:
        alerts.append({
            'severity': 'info',
            'title': 'Alta quantidade de pausas',
            'message': f'{len(high_pause_count_agents)} agentes com mais de {high_pause_count_threshold} pausas',
            'count': len(high_pause_count_agents),
            'threshold': high_pause_count_threshold,
            'type': 'high_pause_count',
        })
    
    return alerts


def detect_no_activity_agents(active_agents_qs: QuerySet, activity_operator_ids: set) -> List[Dict]:
    """
    Detecta agentes ativos sem atividade registrada.
    
    Args:
        active_agents_qs: QuerySet de agentes ativos
        activity_operator_ids: Set de IDs de operadores com atividade
    
    Returns:
        Lista de agentes sem atividade
    """
    no_activity = []
    
    for agent in active_agents_qs:
        if agent.cd_operador not in activity_operator_ids:
            no_activity.append({
                'cd_operador': agent.cd_operador,
                'nm_agente': agent.nm_agente,
                'email': agent.email,
            })
    
    return no_activity[:30]  # Limitar a 30


def calculate_alert_totals(alerts: List[Dict]) -> Dict[str, int]:
    """
    Calcula totais de alertas por severidade.
    
    Args:
        alerts: Lista de alertas
    
    Returns:
        Dicionário com contagem por severidade
    """
    totals = {'crit': 0, 'warn': 0, 'info': 0}
    
    for alert in alerts:
        severity = alert.get('severity', 'info').lower()
        if severity in totals:
            totals[severity] += 1
    
    return totals
