from datetime import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.monitoring.models import Agent, AgentEvent, PauseCategoryChoices, PauseClassification
from apps.monitoring.services.pause_classification import (
    UNCLASSIFIED_CATEGORY,
    list_distinct_event_pause_names,
    list_event_pause_names_by_classification,
    resolve_pause_category,
)


class PauseClassificationTests(TestCase):
    def setUp(self):
        self.agent = Agent.objects.create(cd_operador=500, nm_agente="Agente Teste", ativo=True)
        tz = timezone.get_current_timezone()
        self.base_dt = timezone.make_aware(datetime(2026, 3, 5, 10, 0, 0), tz)

    def _create_pause_event(self, source_event_hash: str, nm_pausa):
        AgentEvent.objects.create(
            source="LH_ALIVE",
            source_event_hash=source_event_hash,
            agent=self.agent,
            cd_operador=self.agent.cd_operador,
            tp_evento="PAUSA",
            nm_pausa=nm_pausa,
            dt_inicio=self.base_dt,
            dt_captura_origem=self.base_dt,
            raw_payload={},
        )

    def test_create_valid_pause_classification(self):
        classification = PauseClassification.objects.create(
            source="lh_alive",
            pause_name="BANHEIRO",
            category=PauseCategoryChoices.NEUTRAL,
            is_active=True,
        )

        self.assertEqual(classification.source, "LH_ALIVE")
        self.assertEqual(classification.pause_name, "BANHEIRO")
        self.assertEqual(classification.pause_name_normalized, "BANHEIRO")
        self.assertEqual(classification.category, PauseCategoryChoices.NEUTRAL)
        self.assertTrue(classification.is_active)

    def test_active_uniqueness_blocks_same_pause_in_other_category(self):
        PauseClassification.objects.create(
            source="",
            pause_name="BANHEIRO",
            category=PauseCategoryChoices.HARMFUL,
            is_active=True,
        )

        with self.assertRaises(ValidationError):
            PauseClassification.objects.create(
                source="",
                pause_name=" banheiro ",
                category=PauseCategoryChoices.LEGAL,
                is_active=True,
            )

    def test_resolve_pause_category_returns_expected_values_and_unclassified(self):
        PauseClassification.objects.create(
            source="",
            pause_name="ALMOCO",
            category=PauseCategoryChoices.LEGAL,
            is_active=True,
        )
        PauseClassification.objects.create(
            source="",
            pause_name="TREINAMENTO",
            category=PauseCategoryChoices.NEUTRAL,
            is_active=True,
        )
        PauseClassification.objects.create(
            source="",
            pause_name="FUMO",
            category=PauseCategoryChoices.HARMFUL,
            is_active=True,
        )

        self.assertEqual(
            resolve_pause_category("  almoco  "),
            PauseCategoryChoices.LEGAL,
        )
        self.assertEqual(
            resolve_pause_category("treinamento"),
            PauseCategoryChoices.NEUTRAL,
        )
        self.assertEqual(
            resolve_pause_category("Fumo"),
            PauseCategoryChoices.HARMFUL,
        )
        self.assertEqual(
            resolve_pause_category("PAUSA_NAO_MAPEADA"),
            UNCLASSIFIED_CATEGORY,
        )

    def test_list_distinct_event_pause_names_ignores_null_and_empty(self):
        self._create_pause_event(source_event_hash="evt-1", nm_pausa="BANHEIRO")
        self._create_pause_event(source_event_hash="evt-2", nm_pausa=" banheiro ")
        self._create_pause_event(source_event_hash="evt-3", nm_pausa="ALMOCO")
        self._create_pause_event(source_event_hash="evt-4", nm_pausa="")
        self._create_pause_event(source_event_hash="evt-5", nm_pausa=None)

        self.assertEqual(list_distinct_event_pause_names(), ["ALMOCO", "BANHEIRO"])

    def test_list_event_pause_names_by_classification_separates_classified_and_unclassified(self):
        self._create_pause_event(source_event_hash="evt-11", nm_pausa="BANHEIRO")
        self._create_pause_event(source_event_hash="evt-12", nm_pausa="ALMOCO")
        self._create_pause_event(source_event_hash="evt-13", nm_pausa="CAFE")

        PauseClassification.objects.create(
            source="",
            pause_name="BANHEIRO",
            category=PauseCategoryChoices.HARMFUL,
            is_active=True,
        )
        PauseClassification.objects.create(
            source="",
            pause_name="CAFE",
            category=PauseCategoryChoices.NEUTRAL,
            is_active=True,
        )

        result = list_event_pause_names_by_classification()
        self.assertEqual(result["classified"], ["BANHEIRO", "CAFE"])
        self.assertEqual(result["unclassified"], ["ALMOCO"])
