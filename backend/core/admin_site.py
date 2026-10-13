from django.contrib.admin import AdminSite

from core.metrics import dashboard_metrics


class MithroAdminSite(AdminSite):
    site_header = "MithroGo Admin"
    site_title = "MithroGo Admin"
    index_title = "Operations dashboard"
    index_template = "core/admin/index.html"

    def index(self, request, extra_context=None):
        context = dict(extra_context or {})
        context["metrics"] = dashboard_metrics()
        return super().index(request, context)
