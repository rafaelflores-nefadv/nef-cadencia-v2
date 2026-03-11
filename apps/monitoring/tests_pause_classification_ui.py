from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.assistant.models import AssistantConversation
from apps.monitoring.models import Agent, AgentEvent, PauseCategoryChoices, PauseClassification


class PauseClassificationConfigViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.staff_user = user_model.objects.create_user(
            username="pause-admin",
            password="secret123",
            is_staff=True,
            is_superuser=True,
        )
        self.regular_user = user_model.objects.create_user(
            username="pause-user",
            password="secret123",
            is_staff=False,
        )
        self.url = reverse("pause-classification-config")
        self.assistant_conversation = AssistantConversation.objects.create(
            created_by=self.staff_user,
            title="Conversa de teste",
        )

        self.agent = Agent.objects.create(cd_operador=501, nm_agente="Operador 501", ativo=True)
        base_dt = timezone.make_aware(datetime(2026, 3, 6, 9, 0, 0), timezone.get_current_timezone())
        pause_names = ["banheiro", "Almoco", " CAFE "]
        for index, pause_name in enumerate(pause_names, start=1):
            event_dt = base_dt + timedelta(minutes=index)
            AgentEvent.objects.create(
                source="LH_ALIVE",
                source_event_hash=f"pause-ui-{index}",
                agent=self.agent,
                cd_operador=self.agent.cd_operador,
                tp_evento="PAUSA",
                nm_pausa=pause_name,
                dt_inicio=event_dt,
                dt_captura_origem=event_dt,
                raw_payload={},
            )

    def test_view_requires_staff_user(self):
        response_anon = self.client.get(self.url)
        self.assertEqual(response_anon.status_code, 302)

        self.client.force_login(self.regular_user)
        response_regular = self.client.get(self.url)
        self.assertEqual(response_regular.status_code, 403)

    def test_route_is_under_admin_monitoring_namespace(self):
        self.assertEqual(self.url, "/admin/monitoring/pause-classification")
        self.client.force_login(self.staff_user)
        legacy_response = self.client.get("/settings/pause-classification")
        self.assertEqual(legacy_response.status_code, 404)

    def test_view_uses_admin_shell_and_dropdown_assets(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nef-admin")
        self.assertContains(response, "js/admin_ui.js")
        self.assertContains(response, "data-admin-group-toggle")

    def test_view_renders_three_operational_columns(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tempo Produtivo")
        self.assertContains(response, "Tempo Neutro")
        self.assertContains(response, "Tempo Improdutivo")
        self.assertContains(response, "Tempo Não Classificado")
        self.assertNotContains(response, "Mover para LEGAL")
        self.assertNotContains(response, "Mover para NEUTRAL")
        self.assertNotContains(response, "Mover para HARMFUL")
        self.assertContains(response, "Adicionar")

    def test_operational_sidebar_does_not_show_pause_classification_link(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("pause-classification-config"))

    def test_admin_menu_shows_custom_pause_classification_link_without_old_model_link(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("pause-classification-config"))
        self.assertNotContains(response, reverse("admin:monitoring_pauseclassification_changelist"))

    def test_admin_changelist_layout_keeps_title_breadcrumb_and_content_order(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("admin:assistant_assistantconversation_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="admin-breadcrumbs"')
        self.assertContains(response, 'id="content-main"')
        html = response.content.decode("utf-8")
        self.assertLess(
            html.find('class="admin-breadcrumbs"'),
            html.find('id="content"'),
        )
        self.assertLess(
            html.find('class="admin-title"'),
            html.find('id="content-main"'),
        )

    def test_admin_changeform_layout_keeps_title_breadcrumb_and_content_order(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(
            reverse(
                "admin:assistant_assistantconversation_change",
                args=[self.assistant_conversation.pk],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="admin-breadcrumbs"')
        self.assertContains(response, 'id="content-main"')
        html = response.content.decode("utf-8")
        self.assertLess(
            html.find('class="admin-breadcrumbs"'),
            html.find('id="content"'),
        )
        self.assertLess(
            html.find('class="admin-title"'),
            html.find('id="content-main"'),
        )

    def test_add_pause_to_category(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(
            self.url,
            {
                "action": "add",
                "category": PauseCategoryChoices.LEGAL,
                "pause_name": "  almoco  ",
            },
        )

        self.assertEqual(response.status_code, 302)
        classification = PauseClassification.objects.get(
            source="",
            pause_name_normalized="ALMOCO",
            is_active=True,
        )
        self.assertEqual(classification.category, PauseCategoryChoices.LEGAL)

    def test_add_prevents_duplicate_active_classification(self):
        PauseClassification.objects.create(
            source="",
            pause_name="BANHEIRO",
            category=PauseCategoryChoices.HARMFUL,
            is_active=True,
        )
        self.client.force_login(self.staff_user)

        response = self.client.post(
            self.url,
            {
                "action": "add",
                "category": PauseCategoryChoices.LEGAL,
                "pause_name": "BANHEIRO",
            },
        )

        self.assertEqual(response.status_code, 302)
        active_rows = PauseClassification.objects.filter(
            source="",
            pause_name_normalized="BANHEIRO",
            is_active=True,
        )
        self.assertEqual(active_rows.count(), 1)
        self.assertEqual(active_rows.first().category, PauseCategoryChoices.HARMFUL)

    def test_remove_classification_sets_inactive(self):
        classification = PauseClassification.objects.create(
            source="",
            pause_name="CAFE",
            category=PauseCategoryChoices.NEUTRAL,
            is_active=True,
        )
        self.client.force_login(self.staff_user)

        response = self.client.post(
            self.url,
            {
                "action": "remove",
                "classification_id": classification.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        classification.refresh_from_db()
        self.assertFalse(classification.is_active)

    def test_move_pause_between_categories(self):
        classification = PauseClassification.objects.create(
            source="",
            pause_name="ALMOCO",
            category=PauseCategoryChoices.LEGAL,
            is_active=True,
        )
        self.client.force_login(self.staff_user)

        response = self.client.post(
            self.url,
            {
                "action": "move",
                "classification_id": classification.id,
                "target_category": PauseCategoryChoices.HARMFUL,
            },
        )

        self.assertEqual(response.status_code, 302)
        classification.refresh_from_db()
        self.assertEqual(classification.category, PauseCategoryChoices.HARMFUL)
        self.assertTrue(classification.is_active)

    def test_removed_pause_returns_to_available_select(self):
        classification = PauseClassification.objects.create(
            source="",
            pause_name="BANHEIRO",
            category=PauseCategoryChoices.HARMFUL,
            is_active=True,
        )
        self.client.force_login(self.staff_user)

        before_remove = self.client.get(self.url)
        self.assertNotIn("BANHEIRO", before_remove.context["available_pause_names"])

        self.client.post(
            self.url,
            {
                "action": "remove",
                "classification_id": classification.id,
            },
        )
        after_remove = self.client.get(self.url)
        self.assertIn("BANHEIRO", after_remove.context["available_pause_names"])

    def test_classified_pauses_do_not_appear_in_select(self):
        PauseClassification.objects.create(
            source="",
            pause_name="ALMOCO",
            category=PauseCategoryChoices.LEGAL,
            is_active=True,
        )
        PauseClassification.objects.create(
            source="",
            pause_name="CAFE",
            category=PauseCategoryChoices.NEUTRAL,
            is_active=True,
        )
        self.client.force_login(self.staff_user)

        response = self.client.get(self.url)
        available = response.context["available_pause_names"]
        self.assertNotIn("ALMOCO", available)
        self.assertNotIn("CAFE", available)
        self.assertIn("BANHEIRO", available)
