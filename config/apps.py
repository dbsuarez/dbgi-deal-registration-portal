from django.contrib.admin.apps import AdminConfig


class DBGIAdminConfig(AdminConfig):
    default_site = "config.admin.DBGIAdminSite"
