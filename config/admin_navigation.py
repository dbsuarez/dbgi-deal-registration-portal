from django.conf import settings


def can_view_registrations(request):
    return request.user.has_perm("registrations.view_registration")


def can_view_rankings(request):
    return request.user.has_perm("registrations.view_opportunityranking")


def can_view_opportunities(request):
    return request.user.has_perm("registrations.view_opportunity")


def can_view_matching_suggestions(request):
    return request.user.has_perm("registrations.view_matchingsuggestion")


def can_view_review_decisions(request):
    return request.user.has_perm("registrations.view_registrationreviewdecision")


def can_view_registration_events(request):
    return request.user.has_perm("registrations.view_registrationevent")


def can_view_companies(request):
    return request.user.has_perm("registrations.view_company")


def can_view_products(request):
    return request.user.has_perm("registrations.view_product")


def can_view_users(request):
    return request.user.has_perm("registrations.view_user")


def can_view_groups(request):
    return request.user.has_perm("auth.view_group")


def can_use_scenario_lab(request):
    return settings.DEBUG and request.user.is_superuser
