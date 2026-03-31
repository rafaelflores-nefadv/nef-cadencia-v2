from django.urls import path

from .views import (
    AgentDetailView,
    AgentListView,
    DashboardAgentsIAView,
    DashboardDataReceivingView,
    DashboardDataSendingView,
    DashboardDayDetailView,
    DashboardPipelineView,
    DashboardProductivityView,
    DashboardRebuildStatsView,
    DashboardRiskView,
    JobRunDetailView,
    JobRunListView,
    PauseClassificationConfigView,
)

urlpatterns = [
    path("dashboard/produtividade", DashboardProductivityView.as_view(), name="dashboard-productivity"),
    path("dashboard/risco", DashboardRiskView.as_view(), name="dashboard-risk"),
    path("dashboard/agentes-ia", DashboardAgentsIAView.as_view(), name="dashboard-agents-ia"),
    path("dashboard/recebimento-dados", DashboardDataReceivingView.as_view(), name="dashboard-data-receiving"),
    path("dashboard/envio-dados", DashboardDataSendingView.as_view(), name="dashboard-data-sending"),
    path("dashboard/pipeline", DashboardPipelineView.as_view(), name="dashboard-pipeline"),
    path("dashboard/day-detail", DashboardDayDetailView.as_view(), name="dashboard-day-detail"),
    path(
        "admin/monitoring/pause-classification",
        PauseClassificationConfigView.as_view(),
        name="pause-classification-config",
    ),
    path(
        "dashboard/actions/rebuild-stats",
        DashboardRebuildStatsView.as_view(),
        name="dashboard-rebuild-day-stats",
    ),
    path("agents", AgentListView.as_view(), name="agents-list"),
    path("agents/<int:pk>", AgentDetailView.as_view(), name="agent-detail"),
    path("runs", JobRunListView.as_view(), name="runs-list"),
    path("runs/<int:pk>", JobRunDetailView.as_view(), name="run-detail"),
]
