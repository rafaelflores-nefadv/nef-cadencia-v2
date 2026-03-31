from django.db.models import Q

from apps.monitoring.models import AgentEvent, PauseClassification

UNCLASSIFIED_CATEGORY = "UNCLASSIFIED"


def normalize_pause_name(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return " ".join(text.split()).upper()


def normalize_source(value: str | None) -> str:
    return str(value or "").strip().upper()


def resolve_pause_category(pause_name: str | None, source: str | None = None) -> str:
    normalized_pause_name = normalize_pause_name(pause_name)
    if not normalized_pause_name:
        return UNCLASSIFIED_CATEGORY

    source_normalized = normalize_source(source)
    base_qs = PauseClassification.objects.filter(
        is_active=True,
        pause_name_normalized=normalized_pause_name,
    )

    if source_normalized:
        category = base_qs.filter(source=source_normalized).values_list("category", flat=True).first()
        if category:
            return category

    global_category = base_qs.filter(source="").values_list("category", flat=True).first()
    return global_category or UNCLASSIFIED_CATEGORY


def list_distinct_event_pause_names(source: str | None = None) -> list[str]:
    event_qs = AgentEvent.objects.filter(nm_pausa__isnull=False).exclude(nm_pausa__exact="")
    if source:
        event_qs = event_qs.filter(source__iexact=str(source).strip())

    normalized_names = {
        normalize_pause_name(pause_name)
        for pause_name in event_qs.values_list("nm_pausa", flat=True)
    }
    normalized_names.discard("")
    return sorted(normalized_names)


def list_event_pause_names_by_classification(source: str | None = None) -> dict[str, list[str]]:
    pause_names = list_distinct_event_pause_names(source=source)
    source_normalized = normalize_source(source)

    classification_qs = PauseClassification.objects.filter(is_active=True)
    if source_normalized:
        classification_qs = classification_qs.filter(Q(source=source_normalized) | Q(source=""))
    else:
        classification_qs = classification_qs.filter(source="")

    classified_names = set(
        classification_qs.values_list("pause_name_normalized", flat=True)
    )

    classified = [pause_name for pause_name in pause_names if pause_name in classified_names]
    unclassified = [pause_name for pause_name in pause_names if pause_name not in classified_names]
    return {
        "classified": classified,
        "unclassified": unclassified,
    }
