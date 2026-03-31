"""
URLs do app core.
"""
from django.urls import path
from .views import SelectWorkspaceView
from .views_settings import SettingsHubView
from .views_settings_pages import (
    SettingsGeneralView,
    SettingsRulesView,
    SettingsIntegrationsView,
    SettingsTemplatesView,
    SettingsAssistantView,
    SettingsPauseClassificationView,
    SettingsUsersView,
    generate_operator_message_api,
)

urlpatterns = [
    # Seleção de workspace (multi-tenant)
    path('select-workspace/', SelectWorkspaceView.as_view(), name='select-workspace'),
    
    # Hub principal
    path('configuracoes/', SettingsHubView.as_view(), name='settings-hub'),
    path('settings/', SettingsHubView.as_view(), name='settings'),  # Alias em inglês
    
    # Páginas filhas de configurações
    path('settings/general/', SettingsGeneralView.as_view(), name='settings-general'),
    path('settings/rules/', SettingsRulesView.as_view(), name='settings-rules'),
    path('settings/integrations/', SettingsIntegrationsView.as_view(), name='settings-integrations'),
    path('settings/templates/', SettingsTemplatesView.as_view(), name='settings-templates'),
    path('settings/assistant/', SettingsAssistantView.as_view(), name='settings-assistant'),
    path('settings/pause-classification/', SettingsPauseClassificationView.as_view(), name='settings-pause-classification'),
    path('settings/users/', SettingsUsersView.as_view(), name='settings-users'),
    path('settings/assistant/generate-message/', generate_operator_message_api, name='generate-operator-message'),
]
