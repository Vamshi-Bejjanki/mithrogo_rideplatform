from django.contrib.admin import AdminSite
from django.urls import path

from core import admin_views, reports
from core.metrics import dashboard_metrics


class MithroAdminSite(AdminSite):
    site_header = "MithroGo Admin"
    site_title = "MithroGo Admin"
    index_title = "Operations dashboard"
    index_template = "core/admin/index.html"

    def get_urls(self):
        custom = [
            path("live-map/", self.admin_view(lambda r: admin_views.live_map(self, r)), name="live_map"),
            path("live-map/data/", self.admin_view(lambda r: admin_views.live_map_data(self, r)), name="live_map_data"),
            path("reports/", self.admin_view(lambda r: admin_views.reports_view(self, r)), name="reports"),
            path("broadcast/", self.admin_view(lambda r: admin_views.broadcast_view(self, r)), name="broadcast"),
        ]
        return custom + super().get_urls()

    def index(self, request, extra_context=None):
        context = dict(extra_context or {})
        context["metrics"] = dashboard_metrics()
        start, end = reports.parse_range(default_days=14)
        context["chart"] = admin_views._chart(reports.daily_report(start, end))
        return super().index(request, context)
