from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False)),
    path('', include('apps.accounts.urls')),
    path('', include('apps.monitoring.urls')),
    path('assistant/', include('apps.assistant.urls')),
    path('admin/', admin.site.urls),
]
