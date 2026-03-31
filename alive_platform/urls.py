from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='dashboard-productivity', permanent=False)),
    path('api/', include('alive_platform.urls_api')),  # API REST
    path('', include('apps.accounts.urls')),
    path('', include('apps.monitoring.urls')),
    path('', include('apps.core.urls')),
    path('', include('apps.rules.urls')),
    path('', include('apps.messaging.urls')),
    path('', include('apps.integrations.urls')),
    path('assistant/', include('apps.assistant.urls')),
    path('admin/', admin.site.urls),
]
