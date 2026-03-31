"""
Service para geração de rankings e leaderboards.

Este service contém a lógica de ordenação e formatação de rankings
de operadores baseados em diferentes métricas.
"""
from typing import List, Dict


def build_pause_rankings(operator_metrics: List[Dict]) -> tuple:
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


def build_productivity_ranking(operator_metrics: List[Dict]) -> List[Dict]:
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


def build_occupancy_ranking(operator_metrics: List[Dict]) -> List[Dict]:
    """
    Gera ranking de taxa de ocupação.
    
    Args:
        operator_metrics: Métricas por operador
    
    Returns:
        Lista ordenada por taxa de ocupação
    """
    ranking = sorted(
        operator_metrics,
        key=lambda x: x.get('taxa_ocupacao_pct', 0),
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
        1: {"name": "Ouro", "emoji": "🥇", "class": "gold"},
        2: {"name": "Prata", "emoji": "🥈", "class": "silver"},
        3: {"name": "Bronze", "emoji": "🥉", "class": "bronze"},
    }
    
    for idx, agent in enumerate(leaderboard_agents, start=1):
        agent['position'] = idx
        agent['medal'] = medals.get(idx)
        
        # Badges baseados em performance
        agent['badges'] = []
        tempo_produtivo = agent.get('tempo_produtivo_seg', 0)
        qtd_pausas = agent.get('qtd_pausas', 0)
        
        if tempo_produtivo > operation_average * 1.2:
            agent['badges'].append({
                'name': 'Destaque',
                'emoji': '⭐',
                'class': 'badge-star'
            })
        
        if qtd_pausas < operation_average * 0.5:
            agent['badges'].append({
                'name': 'Focado',
                'emoji': '🎯',
                'class': 'badge-focus'
            })
        
        if agent.get('taxa_ocupacao_pct', 0) >= 90:
            agent['badges'].append({
                'name': 'Eficiente',
                'emoji': '⚡',
                'class': 'badge-efficient'
            })
    
    return leaderboard_agents


def attach_bar_percentages(ranking: List[Dict], metric_key: str) -> List[Dict]:
    """
    Adiciona percentuais para barras de progresso.
    
    Args:
        ranking: Lista de itens do ranking
        metric_key: Chave da métrica a usar
    
    Returns:
        Ranking com percentuais adicionados
    """
    if not ranking:
        return ranking
    
    # Encontrar valor máximo
    max_value = max(item.get(metric_key, 0) for item in ranking)
    
    if max_value == 0:
        return ranking
    
    # Calcular percentuais
    for item in ranking:
        value = item.get(metric_key, 0)
        item['bar_pct'] = round((value / max_value) * 100, 1)
    
    return ranking
