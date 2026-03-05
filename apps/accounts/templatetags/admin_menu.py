from django import template
from django.conf import settings

register = template.Library()

DEFAULT_ADMIN_MENU_ICONS = {
    "apps": {
        "auth": "shield",
        "accounts": "user-circle",
        "monitoring": "activity",
        "messaging": "mail",
        "integrations": "plug",
        "rules": "settings",
        "reports": "bar-chart-3",
    },
    "models": {
        "auth.user": "user",
        "auth.group": "users",
        "monitoring.agent": "bot",
        "monitoring.jobrun": "activity",
        "messaging.messagetemplate": "mail-check",
        "integrations.integration": "plug-zap",
        "rules.systemconfig": "sliders-horizontal",
    },
}


def _icon_config():
    user_config = getattr(settings, "ADMIN_MENU_ICONS", {})
    app_icons = {}
    model_icons = {}

    if isinstance(user_config, dict):
        app_icons = user_config.get("apps", {}) or {}
        model_icons = user_config.get("models", {}) or {}

    merged_app_icons = {
        **DEFAULT_ADMIN_MENU_ICONS["apps"],
        **{str(k).lower(): str(v) for k, v in app_icons.items()},
    }
    merged_model_icons = {
        **DEFAULT_ADMIN_MENU_ICONS["models"],
        **{str(k).lower(): str(v) for k, v in model_icons.items()},
    }
    return merged_app_icons, merged_model_icons


@register.simple_tag
def admin_app_icon(app_label):
    app_icons, _ = _icon_config()
    return app_icons.get(str(app_label).lower(), "folder")


@register.simple_tag
def admin_model_icon(app_label, model_name):
    app_icons, model_icons = _icon_config()
    app_label = str(app_label).lower()
    model_name = str(model_name).lower()
    model_key = f"{app_label}.{model_name}"
    return model_icons.get(model_key, app_icons.get(app_label, "database"))


@register.simple_tag
def path_startswith(path_value, prefix):
    path_value = str(path_value or "")
    prefix = str(prefix or "")
    if not prefix:
        return False
    return path_value.startswith(prefix)


@register.simple_tag
def admin_app_active(opts, app_label, request_path, app_url):
    opts_label = getattr(opts, "app_label", None)
    if opts_label == str(app_label):
        return True
    return path_startswith(request_path, app_url)


@register.simple_tag
def admin_model_active(opts, app_label, model_name, request_path, model_url):
    opts_app_label = getattr(opts, "app_label", None)
    opts_model_name = getattr(opts, "model_name", None)
    if opts_app_label == str(app_label) and str(opts_model_name or "").lower() == str(model_name).lower():
        return True
    return path_startswith(request_path, model_url)
