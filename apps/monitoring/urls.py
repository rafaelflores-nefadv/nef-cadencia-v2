from django.urls import path

from .views import (
    AgentDetailView,
    AgentListView,
    DashboardDayDetailView,
    DashboardRebuildStatsView,
    DashboardView,
    JobRunDetailView,
    JobRunListView,
    PauseClassificationConfigView,
)

urlpatterns = [
    path("dashboard", DashboardView.as_view(), name="dashboard"),
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
