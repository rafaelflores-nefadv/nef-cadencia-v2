from django.urls import path

from .views import AgentDetailView, AgentListView, DashboardView, JobRunDetailView, JobRunListView

urlpatterns = [
    path("dashboard", DashboardView.as_view(), name="dashboard"),
    path("agents", AgentListView.as_view(), name="agents-list"),
    path("agents/<int:pk>", AgentDetailView.as_view(), name="agent-detail"),
    path("runs", JobRunListView.as_view(), name="runs-list"),
    path("runs/<int:pk>", JobRunDetailView.as_view(), name="run-detail"),
]
