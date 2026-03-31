from dataclasses import dataclass


@dataclass(frozen=True)
class RiskScoringConfig:
    low_occupancy_threshold_pct: float = 65.0
    critical_occupancy_threshold_pct: float = 45.0
    high_harmful_minutes_threshold: int = 90
    critical_harmful_minutes_threshold: int = 180
    high_harmful_events_threshold: int = 5
    high_unclassified_pct_threshold: float = 20.0

    weight_harmful_minutes: float = 1.3
    weight_harmful_events: float = 2.2
    weight_neutral_minutes: float = 0.05
    weight_unclassified_minutes: float = 0.25
    weight_low_occupancy_point: float = 2.6

    extra_harmful_minutes_penalty: float = 35.0
    extra_harmful_events_penalty: float = 18.0
    extra_critical_occupancy_penalty: float = 20.0
    extra_unclassified_attention_penalty: float = 8.0
    no_activity_risk_score: int = 280


DEFAULT_RISK_CONFIG = RiskScoringConfig()


def is_no_activity_metric(metric: dict) -> bool:
    logged_seg = max(0, int(metric.get("tempo_logado_seg") or 0))
    productive_seg = max(0, int(metric.get("tempo_produtivo_seg") or 0))
    relevant_events_count = int(metric.get("qtd_eventos_relevantes") or 0)
    return logged_seg > 0 and productive_seg == 0 and relevant_events_count == 0


def calculate_agent_risk(metric: dict, config: RiskScoringConfig = DEFAULT_RISK_CONFIG) -> dict:
    if is_no_activity_metric(metric):
        return calculate_no_activity_risk(config=config)

    harmful_seg = int(metric.get("tempo_improdutivo_seg") or 0)
    neutral_seg = int(metric.get("tempo_neutro_seg") or 0)
    unclassified_seg = int(metric.get("tempo_nao_classificado_seg") or 0)
    harmful_count = int(metric.get("qtd_improdutivas") or 0)
    occupancy = metric.get("taxa_ocupacao_pct")
    logged_seg = max(0, int(metric.get("tempo_logado_seg") or 0))

    harmful_min = harmful_seg / 60
    neutral_min = neutral_seg / 60
    unclassified_min = unclassified_seg / 60

    # LEGAL/tempo produtivo nao entra na formula de penalizacao.
    score = 0.0
    score += harmful_min * config.weight_harmful_minutes
    score += harmful_count * config.weight_harmful_events
    score += neutral_min * config.weight_neutral_minutes
    score += unclassified_min * config.weight_unclassified_minutes

    reasons: list[str] = []

    if harmful_min >= config.high_harmful_minutes_threshold:
        score += config.extra_harmful_minutes_penalty
        reasons.append("improdutivo alto")
    if harmful_count >= config.high_harmful_events_threshold:
        score += config.extra_harmful_events_penalty
        reasons.append("muitas improdutivas")

    if occupancy is not None and occupancy < config.low_occupancy_threshold_pct:
        score += (config.low_occupancy_threshold_pct - float(occupancy)) * config.weight_low_occupancy_point
        reasons.append("ocupacao baixa")
        if occupancy < config.critical_occupancy_threshold_pct:
            score += config.extra_critical_occupancy_penalty

    unclassified_pct = 0.0
    if logged_seg > 0:
        unclassified_pct = (unclassified_seg / logged_seg) * 100
    if unclassified_pct >= config.high_unclassified_pct_threshold:
        score += config.extra_unclassified_attention_penalty
        reasons.append("nao classificado")

    if not reasons:
        if score <= 0:
            reasons.append("monitorado")
        elif harmful_seg > 0:
            reasons.append("improdutivo")
        elif unclassified_seg > 0:
            reasons.append("nao classificado")
        else:
            reasons.append("monitorado")

    return {
        "risk_score": int(round(score)),
        "primary_reason": reasons[0],
        "reasons": reasons,
        "unclassified_pct": round(unclassified_pct, 2),
    }


def calculate_no_activity_risk(config: RiskScoringConfig = DEFAULT_RISK_CONFIG) -> dict:
    return {
        "risk_score": int(config.no_activity_risk_score),
        "primary_reason": "sem atividade",
        "reasons": ["sem atividade"],
        "unclassified_pct": 0.0,
    }
