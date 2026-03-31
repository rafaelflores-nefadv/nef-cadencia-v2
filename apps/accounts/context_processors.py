from django.contrib.admin.sites import site


def admin_available_apps(request):
    if request.path.startswith("/admin"):
        context = site.each_context(request)
        return {
            "available_apps": context.get("available_apps", []),
        }
    return {}
