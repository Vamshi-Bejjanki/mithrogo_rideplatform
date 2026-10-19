from django.contrib.admin.apps import AdminConfig


class MithroAdminConfig(AdminConfig):
    """Replaces django.contrib.admin so the project uses its own admin site (dashboard, audit)."""

    default_site = "core.admin_site.MithroAdminSite"
