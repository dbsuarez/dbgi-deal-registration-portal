from unfold.sites import UnfoldAdminSite


class DBGIAdminSite(UnfoldAdminSite):
    def has_permission(self, request):
        user = request.user
        return bool(user.is_active and user.is_staff and user.is_dbgi_admin)
