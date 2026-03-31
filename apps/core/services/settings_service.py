"""
Service para agregação de dados do módulo de Configurações.

Este service usa os selectors para buscar dados e aplica lógica de negócio
para determinar status, saúde e alertas das configurações.
"""
from typing import Dict, List
from ..selectors_settings import (
    get_system_configs_stats,
    get_integrations_stats,
    get_message_templates_stats,
    get_pause_classification_stats,
    get_assistant_stats,
    get_users_stats,
    get_operational_rules_stats,
    get_recent_config_changes,
    get_recent_integration_changes,
    get_recent_template_changes,
)


def get_settings_dashboard_data() -> Dict:
    """
    Agrega todos os dados necessários para o dashboard de configurações.
    
    Returns:
        Dict com dados de todas as seções
    """
    return {
        'system_configs': build_system_configs_summary(),
        'operational_rules': build_operational_rules_summary(),
        'integrations': build_integrations_summary(),
        'message_templates': build_message_templates_summary(),
        'assistant_config': build_assistant_summary(),
        'pause_classification': build_pause_classification_summary(),
        'user_management': build_user_management_summary(),
        'appearance': build_appearance_summary(),
        'recent_changes': build_recent_changes_summary(),
    }


def build_system_configs_summary() -> Dict:
    """
    Constrói resumo das configurações gerais do sistema.
    
    Returns:
        Dict com estatísticas e status
    """
    stats = get_system_configs_stats()
    
    # Determinar status
    total = stats['total']
    if total == 0:
        status = 'empty'
    elif total < 5:
        status = 'warning'
    else:
        status = 'active'
    
    return {
        'total': total,
        'categories': stats['categories'],
        'categories_count': stats['categories_count'],
        'last_updated': stats['last_updated'],
        'status': status,
        'health': calculate_config_health(stats),
    }


def build_operational_rules_summary() -> Dict:
    """
    Constrói resumo das regras operacionais.
    
    Returns:
        Dict com estatísticas e status
    """
    stats = get_operational_rules_stats()
    
    total = stats['total']
    status = 'active' if total > 0 else 'empty'
    
    return {
        'total': total,
        'by_prefix': stats['by_prefix'],
        'status': status,
    }


def build_integrations_summary() -> Dict:
    """
    Constrói resumo das integrações.
    
    Returns:
        Dict com estatísticas e status
    """
    stats = get_integrations_stats()
    
    # Determinar status
    total = stats['total']
    enabled = stats['enabled']
    
    if enabled > 0:
        status = 'active'
    elif total > 0:
        status = 'warning'  # Tem integrações mas nenhuma ativa
    else:
        status = 'empty'
    
    # Calcular saúde
    health_score = 0
    if total > 0:
        health_score = int((enabled / total) * 100)
    
    return {
        'total': total,
        'enabled': enabled,
        'disabled': stats['disabled'],
        'by_channel': stats['by_channel'],
        'last_updated': stats['last_updated'],
        'status': status,
        'health_score': health_score,
    }


def build_message_templates_summary() -> Dict:
    """
    Constrói resumo dos templates de mensagens.
    
    Returns:
        Dict com estatísticas e status
    """
    stats = get_message_templates_stats()
    
    # Determinar status
    total = stats['total']
    active = stats['active']
    
    if active > 0:
        status = 'active'
    elif total > 0:
        status = 'warning'  # Tem templates mas nenhum ativo
    else:
        status = 'empty'
    
    # Calcular saúde
    health_score = 0
    if total > 0:
        health_score = int((active / total) * 100)
    
    return {
        'total': total,
        'active': active,
        'inactive': stats['inactive'],
        'by_channel': stats['by_channel'],
        'by_type': stats['by_type'],
        'last_updated': stats['last_updated'],
        'status': status,
        'health_score': health_score,
    }


def build_pause_classification_summary() -> Dict:
    """
    Constrói resumo da classificação de pausas.
    
    Returns:
        Dict com estatísticas e status
    """
    stats = get_pause_classification_stats()
    
    # Determinar status
    total = stats['total']
    active = stats['active']
    
    if active > 0:
        status = 'active'
    elif total > 0:
        status = 'warning'
    else:
        status = 'empty'
    
    # Calcular saúde
    health_score = 0
    if total > 0:
        health_score = int((active / total) * 100)
    
    return {
        'total': total,
        'active': active,
        'inactive': stats['inactive'],
        'by_category': stats['by_category'],
        'by_source': stats['by_source'],
        'status': status,
        'health_score': health_score,
    }


def build_assistant_summary() -> Dict:
    """
    Constrói resumo do assistente IA.
    
    Returns:
        Dict com estatísticas e status
    """
    stats = get_assistant_stats()
    
    # Determinar status
    configs = stats['configs']
    total_conversations = stats['total_conversations']
    
    if configs > 0 and total_conversations > 0:
        status = 'active'
    elif configs > 0:
        status = 'configured'
    else:
        status = 'empty'
    
    return {
        'total_conversations': total_conversations,
        'active_conversations': stats['active_conversations'],
        'total_messages': stats['total_messages'],
        'recent_conversations': stats['recent_conversations'],
        'configs': configs,
        'status': status,
    }


def build_user_management_summary() -> Dict:
    """
    Constrói resumo da gestão de usuários.
    
    Returns:
        Dict com estatísticas e status
    """
    stats = get_users_stats()
    
    # Determinar status
    active_users = stats['active_users']
    
    if active_users > 0:
        status = 'active'
    else:
        status = 'warning'
    
    return {
        'total_users': stats['total_users'],
        'active_users': active_users,
        'staff_users': stats['staff_users'],
        'superusers': stats['superusers'],
        'total_agents': stats['total_agents'],
        'active_agents': stats['active_agents'],
        'status': status,
    }


def build_appearance_summary() -> Dict:
    """
    Constrói resumo de aparência e preferências.
    
    Returns:
        Dict com configurações de aparência
    """
    # Por enquanto, placeholder
    # No futuro, pode incluir temas, cores, logos, etc.
    return {
        'theme': 'default',
        'status': 'active',
    }


def build_recent_changes_summary() -> Dict:
    """
    Constrói resumo das alterações recentes.
    
    Returns:
        Dict com alterações recentes de cada módulo
    """
    return {
        'configs': list(get_recent_config_changes(limit=5)),
        'integrations': list(get_recent_integration_changes(limit=3)),
        'templates': list(get_recent_template_changes(limit=3)),
    }


def calculate_config_health(stats: Dict) -> int:
    """
    Calcula score de saúde das configurações.
    
    Args:
        stats: Estatísticas das configurações
    
    Returns:
        Score de 0 a 100
    """
    total = stats['total']
    categories_count = stats['categories_count']
    
    if total == 0:
        return 0
    
    # Score baseado em quantidade e diversidade
    base_score = min(total * 5, 70)  # Até 70 pontos pela quantidade
    diversity_score = min(categories_count * 10, 30)  # Até 30 pontos pela diversidade
    
    return min(base_score + diversity_score, 100)


def get_settings_health_overview() -> Dict:
    """
    Retorna visão geral da saúde das configurações.
    
    Returns:
        Dict com scores e status geral
    """
    data = get_settings_dashboard_data()
    
    # Calcular scores individuais
    scores = {
        'configs': data['system_configs'].get('health', 0),
        'integrations': data['integrations'].get('health_score', 0),
        'templates': data['message_templates'].get('health_score', 0),
        'pauses': data['pause_classification'].get('health_score', 0),
    }
    
    # Calcular score geral (média ponderada)
    total_score = (
        scores['configs'] * 0.3 +
        scores['integrations'] * 0.25 +
        scores['templates'] * 0.25 +
        scores['pauses'] * 0.2
    )
    
    # Determinar status geral
    if total_score >= 80:
        overall_status = 'excellent'
    elif total_score >= 60:
        overall_status = 'good'
    elif total_score >= 40:
        overall_status = 'fair'
    else:
        overall_status = 'poor'
    
    return {
        'total_score': int(total_score),
        'overall_status': overall_status,
        'scores': scores,
    }


def get_settings_alerts() -> List[Dict]:
    """
    Gera alertas baseados no estado das configurações.
    
    Returns:
        Lista de alertas com severidade e mensagem
    """
    alerts = []
    data = get_settings_dashboard_data()
    
    # Alerta: Nenhuma integração ativa
    integrations = data['integrations']
    if integrations['total'] > 0 and integrations['enabled'] == 0:
        alerts.append({
            'severity': 'warning',
            'title': 'Integrações desabilitadas',
            'message': f'{integrations["total"]} integrações cadastradas mas nenhuma ativa',
            'action_url': '/integracoes/',
            'action_label': 'Gerenciar integrações',
        })
    
    # Alerta: Nenhum template ativo
    templates = data['message_templates']
    if templates['total'] > 0 and templates['active'] == 0:
        alerts.append({
            'severity': 'warning',
            'title': 'Templates inativos',
            'message': f'{templates["total"]} templates cadastrados mas nenhum ativo',
            'action_url': '/templates/',
            'action_label': 'Gerenciar templates',
        })
    
    # Alerta: Poucas configurações
    configs = data['system_configs']
    if configs['total'] < 5:
        alerts.append({
            'severity': 'info',
            'title': 'Poucas configurações',
            'message': 'Sistema tem poucas configurações cadastradas',
            'action_url': '/configuracoes/',
            'action_label': 'Adicionar configurações',
        })
    
    # Alerta: Nenhum usuário staff além do superuser
    users = data['user_management']
    if users['staff_users'] <= 1:
        alerts.append({
            'severity': 'info',
            'title': 'Poucos administradores',
            'message': 'Considere adicionar mais usuários staff',
            'action_url': '/admin/auth/user/',
            'action_label': 'Gerenciar usuários',
        })
    
    return alerts
