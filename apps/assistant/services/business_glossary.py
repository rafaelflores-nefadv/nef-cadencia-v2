from dataclasses import dataclass


SEMANTIC_CATEGORY_RANKING_NEGATIVE = "ranking_negative"
SEMANTIC_CATEGORY_RANKING_POSITIVE = "ranking_positive"
SEMANTIC_CATEGORY_PRODUCTIVITY = "productivity"
SEMANTIC_CATEGORY_IMPRODUCTIVITY = "improductivity"
SEMANTIC_CATEGORY_PAUSE_EXCESS = "pause_excess"
SEMANTIC_CATEGORY_OCCUPANCY = "occupancy"
SEMANTIC_CATEGORY_PERFORMANCE = "performance"
SEMANTIC_CATEGORY_BUSINESS_RULE = "business_rule"
SEMANTIC_CATEGORY_AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class OperationalGlossaryEntry:
    key: str
    category: str
    aliases: tuple[str, ...]
    intent: str
    metric: str | None = None
    ranking_order: str | None = None
    group_by: str | None = None
    default_limit: int | None = None
    business_rule: str | None = None
    requires_business_definition: bool = False
    needs_clarification: bool = False
    clarification_hint: str | None = None
    suggested_interpretation: str | None = None
    criteria: tuple[str, ...] = ()


OPERATIONAL_GLOSSARY = (
    OperationalGlossaryEntry(
        key="worst_agents",
        category=SEMANTIC_CATEGORY_RANKING_NEGATIVE,
        aliases=(
            "piores agentes",
            "pior agente",
            "agentes ruins",
            "agentes que estao ruins",
            "quais agentes estao ruins",
            "quem foi pior",
            "quem esta pior",
            "quem esta puxando a operacao para baixo",
            "quem esta afundando o indicador",
            "quem esta mal no periodo",
            "quem esta mal",
        ),
        intent="productivity_analytics_query",
        metric="improductivity",
        ranking_order="worst",
        group_by="agent",
        default_limit=10,
    ),
    OperationalGlossaryEntry(
        key="best_agents",
        category=SEMANTIC_CATEGORY_RANKING_POSITIVE,
        aliases=(
            "melhores agentes",
            "melhor agente",
            "quem foi melhor",
            "quem esta melhor esse mes",
            "quem esta entregando",
            "quem esta rendendo bem",
            "quem esta rendendo",
        ),
        intent="productivity_analytics_query",
        metric="productivity",
        ranking_order="best",
        group_by="agent",
        default_limit=10,
    ),
    OperationalGlossaryEntry(
        key="poor_performance",
        category=SEMANTIC_CATEGORY_PERFORMANCE,
        aliases=(
            "pior desempenho",
            "desempenho ruim",
            "performando mal",
            "abaixo do esperado",
            "abaixo da regua",
            "baixa ocupacao",
            "ocioso alto",
            "muito parado",
            "fora da curva negativa",
            "desempenho fraco",
            "desempenho mal",
            "quem esta com desempenho ruim",
        ),
        intent="productivity_analytics_query",
        metric="performance",
        ranking_order="worst",
        group_by="agent",
        default_limit=10,
    ),
    OperationalGlossaryEntry(
        key="weak_productivity",
        category=SEMANTIC_CATEGORY_PRODUCTIVITY,
        aliases=(
            "produtividade fraca",
            "menos produtivos",
            "produtividade ruim",
        ),
        intent="productivity_analytics_query",
        metric="productivity",
        ranking_order="worst",
        group_by="agent",
        default_limit=10,
    ),
    OperationalGlossaryEntry(
        key="strong_productivity",
        category=SEMANTIC_CATEGORY_PRODUCTIVITY,
        aliases=(
            "mais produtivos",
            "quem esta melhor",
        ),
        intent="productivity_analytics_query",
        metric="productivity",
        ranking_order="best",
        group_by="agent",
        default_limit=10,
    ),
    OperationalGlossaryEntry(
        key="good_performance",
        category=SEMANTIC_CATEGORY_PERFORMANCE,
        aliases=(
            "desempenho bom",
            "desempenho bem",
            "segurando a operacao",
            "fora da curva positiva",
            "quem esta com desempenho bom",
        ),
        intent="productivity_analytics_query",
        metric="performance",
        ranking_order="best",
        group_by="agent",
        default_limit=10,
    ),
    OperationalGlossaryEntry(
        key="high_improductivity",
        category=SEMANTIC_CATEGORY_IMPRODUCTIVITY,
        aliases=(
            "improdutivo demais",
            "tempo improdutivo alto",
            "quem mais ficou improdutivo",
            "nao esta compensando",
            "nao se pagando",
            "quem esta improdutivo demais",
            "quem esta com tempo improdutivo alto",
            "quem esta com produtividade fraca",
        ),
        intent="productivity_analytics_query",
        metric="improductivity",
        ranking_order="worst",
        group_by="agent",
        default_limit=10,
    ),
    OperationalGlossaryEntry(
        key="high_pause",
        category=SEMANTIC_CATEGORY_PAUSE_EXCESS,
        aliases=(
            "estourando pausa",
            "pausa demais",
            "sobrando em pausa",
            "muita pausa",
            "estourou pausa",
            "quem esta com pausa demais",
            "quem esta estourando pausa",
        ),
        intent="pause_ranking_query",
        group_by="agent",
        default_limit=10,
    ),
    OperationalGlossaryEntry(
        key="payback_in_time",
        category=SEMANTIC_CATEGORY_BUSINESS_RULE,
        aliases=(
            "se pagando em tempo",
            "se pagando no tempo",
            "compensando a operacao",
            "valendo o custo",
            "compensando o salario",
            "dando retorno",
            "se pagando",
        ),
        intent="business_rule_query",
        business_rule="se_pagando_em_tempo",
        requires_business_definition=True,
        clarification_hint="produtividade minima ou retorno esperado no periodo",
        suggested_interpretation="agentes com produtividade acima da meta minima no periodo",
        criteria=(
            "produtividade >= meta_minima",
            "ocupacao >= ocupacao_minima",
            "tempo_improdutivo <= teto_improdutividade",
        ),
    ),
    OperationalGlossaryEntry(
        key="meta_support",
        category=SEMANTIC_CATEGORY_BUSINESS_RULE,
        aliases=(
            "segurando a meta",
            "dentro da meta",
            "acima da meta",
            "acima da regua",
        ),
        intent="business_rule_query",
        business_rule="segurando_meta",
        requires_business_definition=True,
        clarification_hint="qual meta operacional deve ser usada",
        suggested_interpretation="agentes com indicador principal acima da meta cadastrada",
        criteria=("indicador_principal >= meta_operacional",),
    ),
    OperationalGlossaryEntry(
        key="ambiguous_ruim",
        category=SEMANTIC_CATEGORY_AMBIGUOUS,
        aliases=(
            "quem esta ruim",
            "quais estao ruins",
            "ruim no periodo",
            "bom no periodo",
            "folgado",
            "pesado",
            "forte",
            "fraco",
            "compensando",
            "rendendo",
            "quem esta ruim no periodo",
            "quem esta bom no periodo",
        ),
        intent="clarification_query",
        needs_clarification=True,
        clarification_hint="produtividade, improdutividade, pausa ou desempenho",
    ),
)


def iter_glossary_entries() -> tuple[OperationalGlossaryEntry, ...]:
    return OPERATIONAL_GLOSSARY
