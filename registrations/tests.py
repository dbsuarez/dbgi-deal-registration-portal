import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import StringIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import ClassVar
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.admin.models import LogEntry
from django.contrib.admin.sites import AdminSite
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, connection, transaction
from django.test import Client, RequestFactory, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from devtools.models import RegistrationTestPreset

from .admin import RegistrationAdmin
from .audit import registration_change_summary
from .deadlines import process_deadlines
from .maintenance import clear_transactional_records, transactional_record_counts
from .matching import generate_matching_suggestion
from .models import (
    Company,
    CompetitorBrand,
    CompetitorBrandAlias,
    CompetitorItem,
    CompetitorModel,
    EndUser,
    EndUserClassificationOption,
    GeographicArea,
    GeographicDataset,
    NotificationEventSetting,
    Opportunity,
    OpportunityScope,
    PortalSetting,
    PriceApprovalRenewal,
    Product,
    ProductPrice,
    ProjectOutcomeReport,
    PublicHoliday,
    RankingTieDecision,
    Registration,
    RegistrationAttachment,
    RegistrationCategoryApproval,
    RegistrationEvent,
    RegistrationItem,
    RegistrationItemApproval,
    RegistrationNotification,
    RegistrationReviewDecision,
    RepeatOrder,
    User,
)
from .working_days import add_working_days


class RegistrationApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company_a = Company.objects.create(name="North Dealer")
        cls.company_b = Company.objects.create(name="South Dealer")
        cls.user_a = User.objects.create_user(
            username="dealer-a",
            email="dealer-a@example.invalid",
            password="example-password",
            company=cls.company_a,
        )
        cls.user_b = User.objects.create_user(
            username="dealer-b",
            email="dealer-b@example.invalid",
            password="example-password",
            company=cls.company_b,
        )
        cls.admin = User.objects.create_superuser(
            username="dbgi-admin",
            email="admin@example.invalid",
            password="example-password",
        )
        cls.product = Product.objects.create(
            code="TEST-001", name="Test item", category="Test category"
        )
        cls.end_user = EndUser.objects.create(
            official_name="TEST End-user",
            city_municipality="Test City",
            street_address="Test address",
            status=EndUser.Status.VERIFIED,
            created_by=cls.admin,
            verified_by=cls.admin,
        )
        cls.registration_a = cls.make_registration(
            cls.company_a, cls.user_a, "Company A secret project"
        )
        cls.registration_b = cls.make_registration(
            cls.company_b, cls.user_b, "Company B secret project"
        )

    @classmethod
    def make_registration(cls, company, user, title):
        registration = Registration.objects.create(
            company=company,
            submitted_by=user,
            end_user=cls.end_user,
            end_user_name=f"{title} end user",
            end_user_address="Test address",
            project_title=title,
            bid_date=date(2026, 11, 30),
            delivery_date=date(2027, 1, 30),
            contact_person="Test person",
            contact_designation="Buyer",
            contact_email="test@example.invalid",
            contact_number="0000000000",
            evidence_description="Test evidence",
            evidence_sharing_confirmed=True,
        )
        CompetitorItem.objects.create(
            registration=registration,
            brand="Test competitor",
            item_name="Test competitor product",
            bid_price="120.00",
        )
        RegistrationItem.objects.create(
            registration=registration,
            product=cls.product,
            quantity=2,
            requested_unit_price="95.00",
        )
        return registration

    def payload(self, **overrides):
        payload = {
            "end_user_id": self.end_user.pk,
            "project_title": "TEST opportunity",
            "bid_date": "2026-11-30",
            "delivery_date": "2027-01-30",
            "contact_person": "TEST contact",
            "contact_designation": "TEST role",
            "contact_email": "test@example.invalid",
            "contact_number": "0000000000",
            "evidence_description": "TEST evidence description",
            "evidence_url": "",
            "evidence_sharing_confirmed": True,
            "competitor_items": [
                {
                    "brand": "TEST brand",
                    "item_name": "TEST competitor item",
                    "bid_price": "1.00",
                    "remarks": "TEST data",
                }
            ],
            "items": [
                {
                    "product_id": self.product.pk,
                    "non_catalog_name": "",
                    "quantity": 1,
                    "requested_unit_price": "1.00",
                    "justification": "TEST request",
                }
            ],
        }
        payload.update(overrides)
        return payload

    def test_api_requires_authentication_with_standard_error(self):
        response = self.client.get("/api/v1/registrations")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "authentication_required")

    def test_company_can_propose_and_select_a_pending_end_user(self):
        self.client.force_login(self.user_a)
        proposal = {
            "official_name": "City of Sample Procurement Office",
            "acronym": "CSPO",
            "government_branch": "Local government",
            "organization_type": "City",
            "sector": "Government",
            "region": "National Capital Region",
            "province": "Metro Manila",
            "city_municipality": "Sample City",
            "street_address": "123 Public Service Street",
            "postal_code": "1000",
            "philgeps_reference": "TEST-PHILGEPS-001",
            "source_url": "https://notices.philgeps.gov.ph/",
        }

        response = self.client.post(
            "/api/v1/end-users",
            data=json.dumps(proposal),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201, response.content)
        created = response.json()
        self.assertEqual(created["status"], EndUser.Status.PENDING)
        registration_response = self.client.post(
            "/api/v1/registrations",
            data=json.dumps(self.payload(end_user_id=created["id"])),
            content_type="application/json",
        )
        self.assertEqual(registration_response.status_code, 201, registration_response.content)
        registration = Registration.objects.get(pk=registration_response.json()["id"])
        suggestion = registration.matching_suggestions.get(is_current=True)
        self.assertTrue(registration.needs_review)
        self.assertEqual(suggestion.outcome, "clarify")
        self.assertIn("awaiting administrator verification", suggestion.conflicting_factors[0])

    def test_company_cannot_see_another_company_pending_end_user(self):
        pending = EndUser.objects.create(
            official_name="Private pending End-user",
            city_municipality="Test City",
            street_address="Pending Street",
            proposed_by_company=self.company_a,
            created_by=self.user_a,
        )
        self.client.force_login(self.user_b)

        response = self.client.get("/api/v1/end-users")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(pending.pk, {item["id"] for item in response.json()})

    def test_admin_can_verify_end_user_from_django_admin(self):
        pending = EndUser.objects.create(
            official_name="Pending End-user",
            city_municipality="Test City",
            street_address="Pending Street",
            proposed_by_company=self.company_a,
            created_by=self.user_a,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("admin:registrations_enduser_changelist"),
            {"action": "verify_selected", "_selected_action": [pending.pk]},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        pending.refresh_from_db()
        self.assertEqual(pending.status, EndUser.Status.VERIFIED)
        self.assertEqual(pending.verified_by, self.admin)
        self.assertIsNotNone(pending.verified_at)

    def test_equal_top_scores_are_ambiguous_instead_of_first_wins(self):
        target = self.registration_a
        for index in range(2):
            opportunity = Opportunity.objects.create(
                title=f"TEST procurement {index}",
                end_user=self.end_user,
                end_user_name=f"{target.end_user_name} Annex",
                end_user_address=target.end_user_address,
                created_by=self.admin,
            )
            scope = OpportunityScope.objects.create(
                opportunity=opportunity,
                name="Whole opportunity",
                scope_type=OpportunityScope.ScopeType.WHOLE,
            )
            other = self.make_registration(self.company_b, self.user_b, f"TEST other {index}")
            other.status = Registration.Status.ELIGIBLE_MATCHED
            other.opportunity_scope = scope
            other.save(update_fields=["status", "opportunity_scope"])

        suggestion = generate_matching_suggestion(target)

        target.refresh_from_db()
        self.assertGreaterEqual(suggestion.score, 75)
        self.assertEqual(suggestion.outcome, "clarify")
        self.assertEqual(suggestion.confidence, "medium")
        self.assertIsNone(suggestion.candidate_scope_id)
        self.assertIn("2 opportunity scopes scored identically", suggestion.conflicting_factors[0])
        self.assertEqual(target.status, Registration.Status.SUBMITTED)
        self.assertIsNone(target.opportunity_scope_id)

    def test_matching_product_queries_do_not_scale_with_scope_count(self):
        target = self.registration_a
        other_product = Product.objects.create(
            code="TEST-OTHER", name="Other item", category="Test category"
        )

        def add_scope(index):
            opportunity = Opportunity.objects.create(
                title=f"Unrelated procurement {index}",
                end_user=self.end_user,
                end_user_name=f"Unrelated agency {index}",
                end_user_address=f"Unrelated address {index}",
                created_by=self.admin,
            )
            scope = OpportunityScope.objects.create(
                opportunity=opportunity,
                name="Whole opportunity",
                scope_type=OpportunityScope.ScopeType.WHOLE,
            )
            registration = self.make_registration(
                self.company_b, self.user_b, f"Unrelated registration {index}"
            )
            registration.opportunity_scope = scope
            registration.save(update_fields=["opportunity_scope"])
            item = registration.items.get()
            item.product = other_product
            item.save(update_fields=["product"])

        add_scope(0)
        with CaptureQueriesContext(connection) as one_scope_queries:
            generate_matching_suggestion(target)

        for index in range(1, 5):
            add_scope(index)
        with CaptureQueriesContext(connection) as five_scope_queries:
            generate_matching_suggestion(target)

        self.assertEqual(len(five_scope_queries), len(one_scope_queries))

    @override_settings(DEBUG=True)
    def test_development_login_lists_grouped_accounts_and_signs_in(self):
        response = self.client.get("/accounts/login/")
        self.assertContains(response, "/static/registrations/app.css")
        self.assertContains(response, "Company users")
        self.assertContains(response, "DBGI administrators")
        self.assertContains(response, self.user_a.username)
        self.assertContains(response, self.admin.username)

        response = self.client.post(
            "/accounts/debug-login/",
            {"username": self.user_a.username, "next": "/"},
        )

        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user_a.pk)

    @override_settings(DEBUG=False)
    def test_development_login_is_unavailable_outside_debug_mode(self):
        response = self.client.get("/accounts/login/")
        self.assertNotContains(response, "Choose a test account")
        self.assertEqual(
            self.client.post(
                "/accounts/debug-login/", {"username": self.user_a.username}
            ).status_code,
            404,
        )

    @override_settings(LOGIN_THROTTLE_LIMIT=2, LOGIN_THROTTLE_WINDOW_SECONDS=300)
    def test_login_is_throttled_per_normalized_username(self):
        cache.clear()
        credentials = {"username": "  DEALER-A  ", "password": "incorrect"}

        first = self.client.post("/accounts/login/", credentials)
        second = self.client.post("/accounts/login/", credentials)
        limited = self.client.post("/accounts/login/", credentials)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(limited.status_code, 429)
        self.assertEqual(limited["X-RateLimit-Limit"], "2")
        self.assertGreater(int(limited["Retry-After"]), 0)

    @override_settings(
        API_MUTATION_THROTTLE_LIMIT=1,
        API_MUTATION_THROTTLE_WINDOW_SECONDS=60,
    )
    def test_api_mutations_return_standard_rate_limit_error(self):
        cache.clear()
        self.client.force_login(self.user_a)

        first = self.client.post(
            "/api/v1/registrations", data=json.dumps({}), content_type="application/json"
        )
        limited = self.client.post(
            "/api/v1/registrations", data=json.dumps({}), content_type="application/json"
        )

        self.assertEqual(first.status_code, 422)
        self.assertEqual(limited.status_code, 429)
        self.assertEqual(limited.json()["code"], "rate_limited")
        self.assertEqual(limited.json()["details"], [])
        self.assertGreater(int(limited["Retry-After"]), 0)

    @override_settings(THROTTLE_FAIL_CLOSED=True)
    def test_api_mutation_fails_safely_when_throttle_backend_is_unavailable(self):
        self.client.force_login(self.user_a)

        with patch("config.throttling.cache.add", side_effect=ConnectionError):
            response = self.client.post(
                "/api/v1/registrations",
                data=json.dumps({}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "service_unavailable")
        self.assertEqual(response.json()["details"], [])

    @override_settings(DEBUG=True)
    def test_development_account_command_sets_known_local_passwords(self):
        call_command("seed_development_accounts", stdout=StringIO())

        preview = User.objects.get(username="preview")
        admin = User.objects.get(username="admin-preview")
        self.assertTrue(preview.check_password("testpass123"))
        self.assertEqual(preview.role, User.Role.COMPANY)
        self.assertIsNotNone(preview.company_id)
        self.assertTrue(admin.check_password("testpass123"))
        self.assertTrue(admin.is_dbgi_admin)

    @override_settings(DEBUG=False)
    def test_development_account_command_is_blocked_in_production(self):
        with self.assertRaises(CommandError):
            call_command("seed_development_accounts", stdout=StringIO())

    @override_settings(DEBUG=True)
    def test_sample_matching_scenario_is_reproducible(self):
        call_command("seed_development_accounts", stdout=StringIO())
        call_command("seed_sample_matching_scenario", stdout=StringIO())
        call_command("seed_sample_matching_scenario", stdout=StringIO())

        it_user = User.objects.get(username="deals@itavenue.ph")
        lexmark_user = User.objects.get(username="deals@lexmark.com")
        first = Registration.objects.get(company=it_user.company)
        second = Registration.objects.get(company=lexmark_user.company)
        suggestion = second.matching_suggestions.get(is_current=True)
        self.assertLess(first.original_submitted_at, second.original_submitted_at)
        self.assertEqual(first.status, Registration.Status.ELIGIBLE_MATCHED)
        self.assertIsNotNone(first.opportunity_scope_id)
        self.assertEqual(suggestion.outcome, "same_scope")
        self.assertEqual(suggestion.confidence, "high")
        self.assertEqual(suggestion.candidate_scope_id, first.opportunity_scope_id)
        self.assertEqual(suggestion.score, 100)
        self.assertEqual(second.status, Registration.Status.ELIGIBLE_MATCHED)
        self.assertEqual(second.opportunity_scope_id, first.opportunity_scope_id)
        self.assertFalse(second.needs_review)
        self.assertTrue(
            second.events.filter(event_type="Automatically matched", actor=None).exists()
        )

    @override_settings(DEBUG=True)
    def test_automatic_matching_stops_when_two_scopes_match_exactly(self):
        call_command("seed_development_accounts", stdout=StringIO())
        call_command("seed_sample_matching_scenario", stdout=StringIO())
        lexmark = Registration.objects.get(company__name="Lexmark")
        competing_opportunity = Opportunity.objects.create(
            title="A second possible procurement",
            end_user=lexmark.end_user,
            end_user_name=lexmark.end_user_name,
            end_user_address=lexmark.end_user_address,
            created_by=self.admin,
        )
        competing_scope = OpportunityScope.objects.create(
            opportunity=competing_opportunity,
            name="Whole opportunity",
            scope_type=OpportunityScope.ScopeType.WHOLE,
        )
        self.registration_a.status = Registration.Status.ELIGIBLE_MATCHED
        self.registration_a.opportunity_scope = competing_scope
        self.registration_a.save(update_fields=["status", "opportunity_scope"])
        competing_item = self.registration_a.items.get()
        competing_item.product = lexmark.items.get().product
        competing_item.save(update_fields=["product"])
        prior_event_count = lexmark.events.filter(event_type="Automatically matched").count()
        lexmark.status = Registration.Status.SUBMITTED
        lexmark.opportunity_scope = None
        lexmark.save(update_fields=["status", "opportunity_scope"])

        suggestion = generate_matching_suggestion(lexmark)

        lexmark.refresh_from_db()
        self.assertEqual(suggestion.outcome, "clarify")
        self.assertIn(
            "More than one opportunity scope is an exact match.",
            suggestion.conflicting_factors,
        )
        self.assertEqual(lexmark.status, Registration.Status.SUBMITTED)
        self.assertIsNone(lexmark.opportunity_scope_id)
        self.assertEqual(
            lexmark.events.filter(event_type="Automatically matched").count(),
            prior_event_count,
        )

    @override_settings(DEBUG=True)
    def test_admin_ranking_orders_companies_by_original_eligible_time(self):
        call_command("seed_development_accounts", stdout=StringIO())
        call_command("seed_sample_matching_scenario", stdout=StringIO())
        self.client.force_login(self.admin)

        response = self.client.get("/api/v1/rankings")

        self.assertEqual(response.status_code, 200, response.content)
        ranking = response.json()["items"][0]
        self.assertEqual(ranking["participant_count"], 2)
        self.assertEqual(
            [(entry["rank"], entry["company_name"]) for entry in ranking["entries"]],
            [(1, "IT Avenue"), (2, "Lexmark")],
        )

    @override_settings(DEBUG=True)
    def test_company_ranking_exposes_only_its_own_position(self):
        call_command("seed_development_accounts", stdout=StringIO())
        call_command("seed_sample_matching_scenario", stdout=StringIO())
        lexmark_user = User.objects.get(username="deals@lexmark.com")
        self.client.force_login(lexmark_user)

        response = self.client.get("/api/v1/rankings")

        self.assertEqual(response.status_code, 200, response.content)
        ranking = response.json()["items"][0]
        self.assertEqual(ranking["participant_count"], 2)
        self.assertEqual(len(ranking["entries"]), 1)
        self.assertEqual(ranking["entries"][0]["rank"], 2)
        self.assertEqual(ranking["entries"][0]["company_name"], "Lexmark")
        self.assertNotContains(response, "IT Avenue")

    @override_settings(DEBUG=True)
    def test_exact_timestamp_tie_shares_rank(self):
        call_command("seed_development_accounts", stdout=StringIO())
        call_command("seed_sample_matching_scenario", stdout=StringIO())
        first = Registration.objects.get(company__name="IT Avenue")
        second = Registration.objects.get(company__name="Lexmark")
        second.original_submitted_at = first.original_submitted_at
        second.save(update_fields=["original_submitted_at"])
        self.client.force_login(self.admin)

        response = self.client.get("/api/v1/rankings")

        entries = response.json()["items"][0]["entries"]
        self.assertEqual([entry["rank"] for entry in entries], [1, 1])
        self.assertTrue(all(entry["is_tied"] for entry in entries))

    @override_settings(DEBUG=True)
    def test_ranking_counts_each_company_once_per_scope(self):
        call_command("seed_development_accounts", stdout=StringIO())
        call_command("seed_sample_matching_scenario", stdout=StringIO())
        lexmark = Registration.objects.get(company__name="Lexmark")
        duplicate = self.make_registration(
            lexmark.company,
            lexmark.submitted_by,
            "Another employee submission",
        )
        duplicate.status = Registration.Status.ELIGIBLE_MATCHED
        duplicate.opportunity_scope = lexmark.opportunity_scope
        duplicate.original_submitted_at = lexmark.original_submitted_at + timedelta(minutes=1)
        duplicate.save(update_fields=["status", "opportunity_scope", "original_submitted_at"])
        self.client.force_login(self.admin)

        response = self.client.get("/api/v1/rankings")

        ranking = response.json()["items"][0]
        self.assertEqual(ranking["participant_count"], 2)
        self.assertEqual(len(ranking["entries"]), 2)
        self.assertEqual(
            [entry["company_name"] for entry in ranking["entries"]],
            ["IT Avenue", "Lexmark"],
        )

    def test_list_and_detail_are_company_scoped(self):
        self.client.force_login(self.user_a)
        response = self.client.get("/api/v1/registrations?page=1&page_size=10")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 1)
        self.assertEqual(Decimal(response.json()["grand_total"]), Decimal("190.00"))
        self.assertEqual(response.json()["items"][0]["id"], self.registration_a.pk)

        own = self.client.get(f"/api/v1/registrations/{self.registration_a.pk}")
        other = self.client.get(f"/api/v1/registrations/{self.registration_b.pk}")
        self.assertEqual(own.status_code, 200)
        self.assertEqual(len(own.json()["competitor_items"]), 1)
        self.assertEqual(other.status_code, 404)

    def test_admin_can_list_all_registrations(self):
        self.client.force_login(self.admin)
        response = self.client.get("/api/v1/registrations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 2)

    def test_quick_status_filters_are_server_scoped_and_composable(self):
        opportunity = Opportunity.objects.create(
            title="Filtered opportunity",
            end_user=self.end_user,
            end_user_name=self.end_user.official_name,
            end_user_address=self.end_user.full_address,
            project_status=Opportunity.ProjectStatus.ACTIVE,
            created_by=self.admin,
        )
        scope = OpportunityScope.objects.create(
            opportunity=opportunity,
            name="Whole opportunity",
            scope_type=OpportunityScope.ScopeType.WHOLE,
        )
        self.registration_a.opportunity_scope = scope
        self.registration_a.status = Registration.Status.UNDER_REVIEW
        self.registration_a.save(update_fields=["opportunity_scope", "status"])
        self.client.force_login(self.user_a)

        matching = self.client.get(
            "/api/v1/registrations?project_status=active&registration_status=under_review"
        )
        not_matching = self.client.get(
            "/api/v1/registrations?project_status=won&registration_status=under_review"
        )

        self.assertEqual(matching.status_code, 200)
        self.assertEqual(matching.json()["total"], 1)
        self.assertEqual(matching.json()["items"][0]["id"], self.registration_a.pk)
        self.assertEqual(not_matching.status_code, 200)
        self.assertEqual(not_matching.json()["total"], 0)

    def test_company_user_can_reach_admin_login_to_switch_accounts(self):
        self.client.force_login(self.user_a)

        response = self.client.get("/admin/")

        self.assertRedirects(
            response,
            "/admin/login/?next=%2Fadmin%2F",
            fetch_redirect_response=False,
        )

    def test_staff_flag_does_not_grant_company_user_admin_access(self):
        self.user_a.is_staff = True
        self.user_a.save(update_fields=["is_staff"])
        self.client.force_login(self.user_a)

        response = self.client.get("/admin/")

        self.assertRedirects(
            response,
            "/admin/login/?next=%2Fadmin%2F",
            fetch_redirect_response=False,
        )

    def test_dbgi_admin_can_open_django_administration(self):
        RegistrationCategoryApproval.objects.create(
            registration=self.registration_a,
            category=self.product.category,
        )
        EndUser.objects.create(
            official_name="Pending dashboard organization",
            city_municipality="Test City",
            street_address="Pending address",
            created_by=self.admin,
        )
        RegistrationNotification.objects.create(
            recipient=self.user_a,
            registration=self.registration_a,
            event_type=RegistrationNotification.EventType.SUBMISSION_CONFIRMED,
            event_key="dashboard-failed-email",
            title="Submission confirmed",
            message="Registration submitted.",
            email_address=self.user_a.email,
            email_status=RegistrationNotification.EmailStatus.FAILED,
        )
        self.client.force_login(self.admin)

        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/registrations/admin.css")
        self.assertContains(response, "Operations dashboard")
        self.assertContains(response, "Registration review queue")
        self.assertContains(response, self.registration_a.reference)
        self.assertContains(response, "Pricing queue")
        self.assertContains(response, "Pending dashboard organization")
        self.assertContains(response, "Failed email deliveries")
        self.assertContains(response, "Open Danger Zone")

    def test_dashboard_end_user_card_opens_the_pending_filter(self):
        pending = EndUser.objects.create(
            official_name="Only pending dashboard organization",
            city_municipality="Test City",
            street_address="Pending address",
            created_by=self.admin,
        )
        EndUser.objects.create(
            official_name="Rejected dashboard organization",
            city_municipality="Test City",
            street_address="Rejected address",
            status=EndUser.Status.REJECTED,
            created_by=self.admin,
        )
        self.client.force_login(self.admin)

        dashboard = self.client.get("/admin/")

        self.assertEqual(dashboard.context["pending_end_user_count"], 1)
        self.assertEqual(
            dashboard.context["end_user_list_url"],
            "/admin/registrations/enduser/?status__exact=pending",
        )

        filtered_list = self.client.get(dashboard.context["end_user_list_url"])

        self.assertEqual(filtered_list.status_code, 200)
        self.assertContains(filtered_list, pending.official_name)
        self.assertNotContains(filtered_list, self.end_user.official_name)
        self.assertNotContains(filtered_list, "Rejected dashboard organization")
        self.assertContains(filtered_list, "Clear all filters")

        cleared_list = self.client.get("/admin/registrations/enduser/")

        self.assertContains(cleared_list, pending.official_name)
        self.assertContains(cleared_list, self.end_user.official_name)
        self.assertContains(cleared_list, "Rejected dashboard organization")

    def test_danger_zone_requires_a_superuser(self):
        reviewer = User.objects.create_user(
            username="danger-zone-reviewer",
            password="example-password",
            role=User.Role.DBGI_ADMIN,
            is_staff=True,
        )
        self.client.force_login(reviewer)

        index = self.client.get("/admin/")
        response = self.client.get(reverse("admin:danger-zone"))

        self.assertNotContains(index, "Open Danger Zone")
        self.assertEqual(response.status_code, 404)

    def test_danger_zone_requires_csrf_and_exact_confirmation(self):
        url = reverse("admin:danger-zone")
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.admin)

        rejected = csrf_client.post(
            url,
            {
                "acknowledge": "on",
                "confirmation": "DELETE ALL TRANSACTIONAL DATA",
            },
        )
        self.assertEqual(rejected.status_code, 403)

        self.client.force_login(self.admin)
        wrong_phrase = self.client.post(
            url,
            {"acknowledge": "on", "confirmation": "delete everything"},
        )
        missing_acknowledgement = self.client.post(
            url,
            {"confirmation": "DELETE ALL TRANSACTIONAL DATA"},
        )

        self.assertContains(wrong_phrase, "Type DELETE ALL TRANSACTIONAL DATA exactly")
        self.assertContains(
            missing_acknowledgement,
            "Confirm that you understand this action cannot be undone",
        )
        self.assertTrue(Registration.objects.filter(pk=self.registration_a.pk).exists())

    def test_danger_zone_clears_transactions_and_preserves_master_data(self):
        opportunity = Opportunity.objects.create(
            title="Danger Zone test opportunity",
            end_user=self.end_user,
            end_user_name=self.end_user.official_name,
            end_user_address=self.end_user.full_address,
            created_by=self.admin,
        )
        scope = OpportunityScope.objects.create(
            opportunity=opportunity,
            name="Whole opportunity",
            scope_type=OpportunityScope.ScopeType.WHOLE,
        )
        self.registration_a.opportunity_scope = scope
        self.registration_a.save(update_fields=["opportunity_scope"])
        approval = RegistrationCategoryApproval.objects.create(
            registration=self.registration_a,
            category=self.product.category,
        )
        RegistrationItemApproval.objects.create(
            category_approval=approval,
            registration_item=self.registration_a.items.get(),
            approved_unit_price="90.00",
        )
        PriceApprovalRenewal.objects.create(
            category_approval=approval,
            requested_by=self.user_a,
            reason="Test renewal",
        )
        RegistrationNotification.objects.create(
            recipient=self.user_a,
            registration=self.registration_a,
            event_type=RegistrationNotification.EventType.SUBMISSION_CONFIRMED,
            event_key="danger-zone-test",
            title="Submission confirmed",
            message="Test notification",
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("admin:danger-zone"),
            {
                "acknowledge": "on",
                "confirmation": "DELETE ALL TRANSACTIONAL DATA",
            },
        )

        self.assertContains(response, "All registration transactional data was deleted")
        self.assertFalse(Registration.objects.exists())
        self.assertFalse(Opportunity.objects.exists())
        self.assertFalse(OpportunityScope.objects.exists())
        self.assertFalse(RegistrationCategoryApproval.objects.exists())
        self.assertFalse(RegistrationItemApproval.objects.exists())
        self.assertFalse(PriceApprovalRenewal.objects.exists())
        self.assertFalse(RegistrationNotification.objects.exists())
        self.assertTrue(Company.objects.filter(pk=self.company_a.pk).exists())
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())
        self.assertTrue(EndUser.objects.filter(pk=self.end_user.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.user_a.pk).exists())
        self.assertTrue(
            LogEntry.objects.filter(
                user=self.admin,
                object_repr="All registration transactional data",
            ).exists()
        )

    @override_settings(DEBUG=True)
    def test_django_admin_shows_read_only_opportunity_rankings(self):
        call_command("seed_development_accounts", stdout=StringIO())
        call_command("seed_sample_matching_scenario", stdout=StringIO())
        it_avenue = Registration.objects.get(company__name="IT Avenue")
        lexmark = Registration.objects.get(company__name="Lexmark")
        self.client.force_login(self.admin)

        index = self.client.get("/admin/")
        rankings = self.client.get(reverse("admin:registrations_opportunityranking_changelist"))

        self.assertContains(index, "Opportunity rankings")
        self.assertEqual(rankings.status_code, 200, rankings.content)
        self.assertContains(rankings, "IT Avenue")
        self.assertContains(rankings, "Lexmark")
        self.assertContains(rankings, it_avenue.reference)
        self.assertContains(rankings, lexmark.reference)

    @override_settings(DEBUG=True)
    def test_superuser_scenario_lab_loads_each_documented_scenario(self):
        self.client.force_login(self.admin)
        url = reverse("admin:devtools_scenariolab_changelist")

        index = self.client.get("/admin/")
        lab = self.client.get(url)

        self.assertContains(index, "Transactions")
        self.assertContains(index, "Master data")
        self.assertContains(index, "Administration")
        self.assertContains(index, "Scenario Lab")
        self.assertContains(lab, "Automatic exact match")
        self.assertContains(lab, "Ambiguous exact match")
        self.assertContains(lab, "Material edit after matching")

        expectations = {
            "automatic_exact": (
                "QCS printer lot later registration",
                Registration.Status.ELIGIBLE_MATCHED,
            ),
            "ambiguous_match": (
                "Pasig printer ambiguity later registration",
                Registration.Status.SUBMITTED,
            ),
            "material_edit": (
                "Makati printer edit later registration",
                Registration.Status.REVIEW_REQUIRED,
            ),
        }
        for scenario, (title, status) in expectations.items():
            with self.subTest(scenario=scenario):
                response = self.client.post(
                    url,
                    {
                        "scenario": scenario,
                        "clear_transactional": "on",
                        "confirmation": "CLEAR TRANSACTIONS",
                    },
                )
                self.assertEqual(response.status_code, 200, response.content)
                registration = Registration.objects.get(project_title=title)
                self.assertEqual(registration.status, status)
                self.assertContains(response, "Scenario loaded")

        self.assertTrue(Company.objects.filter(pk=self.company_a.pk).exists())
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.user_a.pk).exists())

    @override_settings(DEBUG=True)
    def test_scenario_lab_requires_exact_clear_confirmation(self):
        self.client.force_login(self.admin)
        url = reverse("admin:devtools_scenariolab_changelist")

        response = self.client.post(
            url,
            {
                "scenario": "automatic_exact",
                "clear_transactional": "on",
                "confirmation": "clear",
            },
        )

        self.assertContains(response, "Type CLEAR TRANSACTIONS exactly")
        self.assertTrue(Registration.objects.filter(pk=self.registration_a.pk).exists())

    @override_settings(DEBUG=True)
    def test_scenario_lab_is_hidden_from_non_superuser_admin(self):
        reviewer = User.objects.create_user(
            username="reviewer",
            password="example-password",
            role=User.Role.DBGI_ADMIN,
            is_staff=True,
        )
        self.client.force_login(reviewer)

        index = self.client.get("/admin/")
        lab = self.client.get(reverse("admin:devtools_scenariolab_changelist"))

        self.assertNotContains(index, "Scenario Lab")
        self.assertEqual(lab.status_code, 404)

    @override_settings(DEBUG=False)
    def test_scenario_lab_is_unavailable_outside_debug_mode(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin:devtools_scenariolab_changelist"))

        self.assertEqual(response.status_code, 404)

    @override_settings(DEBUG=True)
    def test_session_and_product_options(self):
        self.user_a.first_name = "Dante"
        self.user_a.last_name = "Suarez Jr"
        self.user_a.email = "dante.suarez@example.invalid"
        self.user_a.designation = "Product Specialist"
        self.user_a.phone_number = "09227667968"
        self.user_a.save(
            update_fields=[
                "first_name",
                "last_name",
                "email",
                "designation",
                "phone_number",
            ]
        )
        self.client.force_login(self.user_a)
        session = self.client.get("/api/v1/session")
        products = self.client.get("/api/v1/products")
        self.assertEqual(session.status_code, 200)
        self.assertTrue(session.json()["csrf_token"])
        self.assertEqual(session.json()["display_name"], "Dante Suarez Jr")
        self.assertEqual(session.json()["email"], "dante.suarez@example.invalid")
        self.assertEqual(session.json()["designation"], "Product Specialist")
        self.assertEqual(session.json()["phone_number"], "09227667968")
        self.assertTrue(session.json()["is_debug"])
        self.assertTrue(session.json()["end_user_field_help_available"])
        self.assertTrue(session.json()["show_end_user_field_help"])
        self.assertEqual(products.status_code, 200)
        self.assertIn(self.product.code, {item["code"] for item in products.json()})

    @override_settings(DEBUG=False)
    def test_session_disables_development_helpers_outside_debug_mode(self):
        self.client.force_login(self.user_a)

        response = self.client.get("/api/v1/session")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_debug"])

    def test_superuser_can_toggle_end_user_field_help(self):
        setting = PortalSetting.objects.get(key="portal")
        changelist_url = reverse("admin:registrations_portalsetting_changelist")

        self.client.force_login(self.user_a)
        self.assertEqual(self.client.get(changelist_url).status_code, 302)

        setting.show_end_user_field_help = False
        setting.save(update_fields=["show_end_user_field_help", "updated_at"])
        response = self.client.get("/api/v1/session")
        self.assertFalse(response.json()["end_user_field_help_available"])
        self.assertFalse(response.json()["show_end_user_field_help"])

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(changelist_url).status_code, 200)

    def test_user_can_save_end_user_field_help_preference(self):
        self.client.force_login(self.user_a)

        response = self.client.put(
            "/api/v1/session/preferences/end-user-field-help",
            data=json.dumps({"show_end_user_field_help": False}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["show_end_user_field_help"])
        self.user_a.refresh_from_db()
        self.assertFalse(self.user_a.show_end_user_field_help)
        self.assertFalse(self.client.get("/api/v1/session").json()["show_end_user_field_help"])

    def test_global_setting_overrides_user_end_user_field_help_preference(self):
        setting = PortalSetting.objects.get(key="portal")
        setting.show_end_user_field_help = False
        setting.save(update_fields=["show_end_user_field_help", "updated_at"])
        self.client.force_login(self.user_a)

        response = self.client.put(
            "/api/v1/session/preferences/end-user-field-help",
            data=json.dumps({"show_end_user_field_help": True}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["show_end_user_field_help"])
        self.user_a.refresh_from_db()
        self.assertTrue(self.user_a.show_end_user_field_help)

    @override_settings(DEBUG=True)
    def test_debug_users_share_registration_test_presets(self):
        self.client.force_login(self.user_a)
        create_response = self.client.post(
            "/api/v1/development/registration-test-presets",
            data=json.dumps(
                {
                    "name": "My reusable test",
                    "description": "Development only",
                    "payload": self.payload(),
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(create_response.status_code, 201, create_response.content)
        self.assertEqual(create_response.json()["created_by_name"], "dealer-a")
        preset_id = create_response.json()["id"]
        self.user_b.first_name = "Bianca"
        self.user_b.last_name = "Reyes"
        self.user_b.save(update_fields=["first_name", "last_name"])
        other_preset = RegistrationTestPreset.objects.create(
            owner=self.user_b,
            name="Other user's test",
            payload=self.payload(),
        )
        list_response = self.client.get("/api/v1/development/registration-test-presets")
        self.assertEqual(
            [(item["name"], item["created_by_name"]) for item in list_response.json()],
            [("My reusable test", "dealer-a"), ("Other user's test", "Bianca Reyes")],
        )

        self.client.force_login(self.user_b)
        updated_payload = self.payload(project_title="Updated test project")
        update_response = self.client.put(
            f"/api/v1/development/registration-test-presets/{preset_id}",
            data=json.dumps(
                {
                    "name": "My reusable test",
                    "description": "Updated",
                    "payload": updated_payload,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.content)
        self.assertEqual(
            update_response.json()["payload"]["project_title"],
            "Updated test project",
        )
        self.assertEqual(update_response.json()["created_by_name"], "dealer-a")

        delete_response = self.client.delete(
            f"/api/v1/development/registration-test-presets/{preset_id}"
        )
        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(RegistrationTestPreset.objects.filter(pk=preset_id).exists())

        delete_other_response = self.client.delete(
            f"/api/v1/development/registration-test-presets/{other_preset.pk}"
        )
        self.assertEqual(delete_other_response.status_code, 204)

    @override_settings(DEBUG=False)
    def test_registration_test_presets_are_unavailable_outside_debug_mode(self):
        self.client.force_login(self.user_a)

        response = self.client.get("/api/v1/development/registration-test-presets")

        self.assertEqual(response.status_code, 404)

    def test_competitor_brand_options_return_active_master_data(self):
        CompetitorBrand.objects.create(name="Active brand")
        CompetitorBrand.objects.create(name="Archived brand", is_active=False)
        self.client.force_login(self.user_a)
        response = self.client.get("/api/v1/competitor-brands")

        self.assertEqual(response.status_code, 200)
        self.assertTrue({"Canon", "Epson", "HP", "Lexmark"}.issubset(response.json()))
        self.assertIn("Active brand", response.json())
        self.assertNotIn("Archived brand", response.json())

    def test_geographic_options_are_filtered_by_psgc_hierarchy(self):
        region = GeographicArea.objects.create(
            code="1300000000",
            name="National Capital Region (NCR)",
            level=GeographicArea.Level.REGION,
            region_code="1300000000",
        )
        GeographicArea.objects.create(
            code="1307400000",
            name="City of Pasig",
            level=GeographicArea.Level.CITY_MUNICIPALITY,
            region_code=region.code,
            city_municipality_code="1307400000",
            postal_code="1600",
        )
        GeographicDataset.objects.create(
            version="TEST-PSGC",
            source_url="https://example.invalid/psgc",
        )
        self.client.force_login(self.user_a)

        regions = self.client.get("/api/v1/geographic-areas?level=region")
        cities = self.client.get(
            "/api/v1/geographic-areas?level=city_municipality&region_code=1300000000"
        )
        dataset = self.client.get("/api/v1/geographic-dataset")

        self.assertEqual(regions.status_code, 200)
        self.assertEqual(regions.json()[0]["name"], region.name)
        self.assertEqual(cities.status_code, 200)
        self.assertEqual(cities.json()[0]["postal_code"], "1600")
        self.assertEqual(dataset.json()["version"], "TEST-PSGC")

    def test_company_sees_approved_and_own_pending_classifications(self):
        EndUserClassificationOption.objects.create(
            category=EndUserClassificationOption.Category.ORGANIZATION_TYPE,
            name="Approved type",
            status=EndUserClassificationOption.Status.APPROVED,
        )
        EndUserClassificationOption.objects.create(
            category=EndUserClassificationOption.Category.ORGANIZATION_TYPE,
            name="Dealer A proposal",
            proposed_by_company=self.company_a,
        )
        EndUserClassificationOption.objects.create(
            category=EndUserClassificationOption.Category.ORGANIZATION_TYPE,
            name="Dealer B proposal",
            proposed_by_company=self.company_b,
        )
        self.client.force_login(self.user_a)

        response = self.client.get("/api/v1/end-user-classifications?category=organization_type")

        self.assertEqual(response.status_code, 200)
        names = {item["name"] for item in response.json()}
        self.assertIn("Approved type", names)
        self.assertIn("Dealer A proposal", names)
        self.assertNotIn("Dealer B proposal", names)

    def test_new_end_user_proposes_missing_classification_values(self):
        self.client.force_login(self.user_a)
        payload = {
            "official_name": "New City Office",
            "government_branch": "Local government",
            "organization_type": "City procurement office",
            "sector": "Procurement",
            "city_municipality": "City of Pasig",
            "street_address": "City Hall Complex",
        }

        response = self.client.post(
            "/api/v1/end-users",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        proposals = EndUserClassificationOption.objects.filter(
            proposed_by_company=self.company_a,
            status=EndUserClassificationOption.Status.PENDING,
        )
        self.assertEqual(
            set(proposals.values_list("category", "name")),
            {
                ("organization_type", "City procurement office"),
                ("sector", "Procurement"),
            },
        )

    def test_new_end_user_rejects_unknown_government_branch(self):
        self.client.force_login(self.user_a)
        payload = {
            "official_name": "New City Office",
            "government_branch": "LGU",
            "city_municipality": "City of Pasig",
            "street_address": "City Hall Complex",
        }

        response = self.client.post(
            "/api/v1/end-users",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_government_branch")

    def test_registration_adds_new_competitor_brand_to_master_data(self):
        self.client.force_login(self.user_a)
        payload = self.payload()
        payload["competitor_items"][0]["brand"] = "  New Brand  "
        payload["competitor_items"][0]["item_name"] = "  New Model  "

        response = self.client.post(
            "/api/v1/registrations",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201, response.content)
        brand = CompetitorBrand.objects.get(normalized_name="new brand")
        self.assertEqual(brand.name, "New Brand")
        competitor_model = CompetitorModel.objects.get(brand=brand, normalized_name="new model")
        self.assertEqual(competitor_model.name, "New Model")
        registration = Registration.objects.get(pk=response.json()["id"])
        self.assertEqual(registration.competitor_items.get().item_name, "New Model")

    def test_competitor_model_options_return_only_active_master_data(self):
        canon = CompetitorBrand.objects.get(normalized_name="canon")
        active_model = CompetitorModel.objects.create(brand=canon, name="Active test model")
        CompetitorModel.objects.create(brand=canon, name="Archived test model", is_active=False)
        archived_brand = CompetitorBrand.objects.create(
            name="Archived model brand", is_active=False
        )
        CompetitorModel.objects.create(brand=archived_brand, name="Hidden model")
        self.client.force_login(self.user_a)

        response = self.client.get("/api/v1/competitor-models")

        self.assertEqual(response.status_code, 200)
        options = {(item["brand"], item["item_name"]) for item in response.json()}
        self.assertIn(("Canon", "imageCLASS LBP246dw"), options)
        self.assertIn(("Canon", active_model.name), options)
        self.assertNotIn(("Canon", "Archived test model"), options)
        self.assertNotIn((archived_brand.name, "Hidden model"), options)

    def test_competitor_brand_alias_resolves_to_canonical_brand(self):
        self.client.force_login(self.user_a)
        payload = self.payload()
        payload["competitor_items"][0]["brand"] = "  hewlett PACKARD  "
        payload["competitor_items"][0]["item_name"] = "  laserjet PRO 4003DN  "

        response = self.client.post(
            "/api/v1/registrations",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201, response.content)
        registration = Registration.objects.get(pk=response.json()["id"])
        self.assertEqual(registration.competitor_items.get().brand, "HP")
        self.assertEqual(registration.competitor_items.get().item_name, "LaserJet Pro 4003dn")
        self.assertEqual(
            CompetitorModel.objects.filter(
                brand__normalized_name="hp",
                normalized_name="laserjet pro 4003dn",
            ).count(),
            1,
        )
        self.assertFalse(CompetitorBrand.objects.filter(normalized_name="hewlett packard").exists())

    def test_competitor_brand_normalized_name_is_database_unique(self):
        CompetitorBrand.objects.create(name="Unique Brand")

        with self.assertRaises(IntegrityError), transaction.atomic():
            CompetitorBrand.objects.bulk_create(
                [CompetitorBrand(name="Duplicate spelling", normalized_name="unique brand")]
            )

    def test_competitor_brand_admin_is_restricted_and_supports_aliases(self):
        hp = CompetitorBrand.objects.get(normalized_name="hp")
        self.assertTrue(
            CompetitorBrandAlias.objects.filter(
                brand=hp, normalized_name="hewlett packard"
            ).exists()
        )
        changelist_url = reverse("admin:registrations_competitorbrand_changelist")

        self.client.force_login(self.user_a)
        self.assertEqual(self.client.get(changelist_url).status_code, 302)

        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin:registrations_competitorbrand_change", args=[hp.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hewlett Packard")
        self.assertContains(response, "LaserJet Pro 4003dn")

        model_changelist_url = reverse("admin:registrations_competitormodel_changelist")
        self.assertEqual(self.client.get(model_changelist_url).status_code, 200)

    def test_category_approval_admin_offers_only_its_registration_items(self):
        approval = RegistrationCategoryApproval.objects.create(
            registration=self.registration_a,
            category=self.product.category,
        )
        own_item = self.registration_a.items.get()
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("admin:registrations_registrationcategoryapproval_change", args=[approval.pk])
        )

        self.assertEqual(response.status_code, 200)
        item_field = response.context["inline_admin_formsets"][0].formset.empty_form.fields[
            "registration_item"
        ]
        self.assertEqual(list(item_field.queryset), [own_item])
        self.assertEqual(
            item_field.label_from_instance(own_item),
            f"{self.registration_a.reference} - {own_item}",
        )
        form_fields = response.context["adminform"].form.fields
        self.assertNotIn("reviewed_by", form_fields)
        self.assertNotIn("reviewed_at", form_fields)

    def test_logout_ends_authenticated_session(self):
        self.client.force_login(self.user_a)

        response = self.client.post("/api/v1/session/logout")

        self.assertEqual(response.status_code, 204)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.get("/api/v1/session").status_code, 401)

    def test_logout_accepts_local_react_development_origin(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user_a)
        csrf_token = client.get("/api/v1/session").json()["csrf_token"]

        response = client.post(
            "/api/v1/session/logout",
            HTTP_ORIGIN="http://127.0.0.1:5173",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 204)

    def test_create_registration_saves_scope_children_and_audit(self):
        self.client.force_login(self.user_a)
        response = self.client.post(
            "/api/v1/registrations",
            data=json.dumps(self.payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        registration = Registration.objects.get(project_title="TEST opportunity")
        self.assertEqual(registration.company, self.company_a)
        self.assertEqual(registration.competitor_items.count(), 1)
        self.assertEqual(registration.items.count(), 1)
        self.assertEqual(registration.events.get().event_type, "Submitted")
        self.assertEqual(registration.matching_suggestions.filter(is_current=True).count(), 1)

    def test_submission_notifies_each_active_company_user_once(self):
        colleague = User.objects.create_user(
            username="dealer-a-colleague",
            password="example-password",
            company=self.company_a,
        )
        inactive = User.objects.create_user(
            username="dealer-a-inactive",
            password="example-password",
            company=self.company_a,
            is_active=False,
        )
        self.client.force_login(self.user_a)

        first = self.client.post(
            "/api/v1/registrations",
            data=json.dumps(self.payload()),
            content_type="application/json",
        )

        self.assertEqual(first.status_code, 201, first.content)
        registration = Registration.objects.get(pk=first.json()["id"])
        recipients = set(
            RegistrationNotification.objects.filter(
                registration=registration,
                event_type=RegistrationNotification.EventType.SUBMISSION_CONFIRMED,
            ).values_list("recipient__username", flat=True)
        )
        self.assertEqual(recipients, {self.user_a.username, colleague.username})
        self.assertNotIn(inactive.username, recipients)
        self.assertNotIn(self.user_b.username, recipients)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="portal@example.invalid",
        PORTAL_BASE_URL="https://registration.example.invalid",
    )
    def test_submission_email_is_sent_after_commit_without_sensitive_details(self):
        NotificationEventSetting.objects.update_or_create(
            event_type=RegistrationNotification.EventType.SUBMISSION_CONFIRMED,
            defaults={
                "email_enabled": True,
                "email_subject_template": "Registration update: {registration_reference}",
                "email_body_template": "{title}\n{message}\nView: {portal_url}/notifications/",
            },
        )
        self.client.force_login(self.user_a)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                "/api/v1/registrations",
                data=json.dumps(self.payload()),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 201, response.content)
        partner_mail = [m for m in mail.outbox if m.to == [self.user_a.email]]
        self.assertEqual(len(partner_mail), 1)
        email = partner_mail[0]
        self.assertEqual(
            email.subject,
            f"Registration update: DBGI-{response.json()['id']:06d}",
        )
        self.assertIn("/notifications/", email.body)
        self.assertNotIn("TEST brand", email.body)
        self.assertNotIn("1.00", email.body)
        notice = RegistrationNotification.objects.get(
            registration_id=response.json()["id"],
            recipient=self.user_a,
            event_type=RegistrationNotification.EventType.SUBMISSION_CONFIRMED,
        )
        self.assertEqual(notice.email_status, RegistrationNotification.EmailStatus.SENT)
        self.assertEqual(notice.email_attempts, 1)
        self.assertEqual(notice.email_address, self.user_a.email)
        self.assertEqual(notice.email_subject, email.subject)
        self.assertEqual(notice.email_body, email.body)

    def test_notification_email_template_rejects_unknown_placeholders(self):
        setting = NotificationEventSetting(
            event_type=RegistrationNotification.EventType.PRICE_DECISION,
            email_subject_template="Price decision for {company_secret}",
        )

        with self.assertRaises(ValidationError) as context:
            setting.full_clean()

        self.assertIn("email_subject_template", context.exception.message_dict)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_failure_does_not_rollback_the_portal_notification(self):
        NotificationEventSetting.objects.update_or_create(
            event_type=RegistrationNotification.EventType.SUBMISSION_CONFIRMED,
            defaults={"email_enabled": True},
        )
        self.client.force_login(self.user_a)

        with patch(
            "registrations.notifications.EmailMessage.send",
            side_effect=ConnectionError("SMTP unavailable"),
        ):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    "/api/v1/registrations",
                    data=json.dumps(self.payload()),
                    content_type="application/json",
                )

        self.assertEqual(response.status_code, 201, response.content)
        notice = RegistrationNotification.objects.get(
            registration_id=response.json()["id"],
            recipient=self.user_a,
            event_type=RegistrationNotification.EventType.SUBMISSION_CONFIRMED,
        )
        self.assertEqual(notice.email_status, RegistrationNotification.EmailStatus.FAILED)
        self.assertEqual(notice.email_attempts, 1)
        self.assertIn("SMTP unavailable", notice.email_error)

    def test_notification_inbox_is_recipient_scoped_and_read_is_idempotent(self):
        own = RegistrationNotification.objects.create(
            recipient=self.user_a,
            registration=self.registration_a,
            event_type=RegistrationNotification.EventType.SUBMISSION_CONFIRMED,
            event_key="test-own",
            title="Submission confirmed",
            message="The registration was submitted.",
        )
        other = RegistrationNotification.objects.create(
            recipient=self.user_b,
            registration=self.registration_b,
            event_type=RegistrationNotification.EventType.SUBMISSION_CONFIRMED,
            event_key="test-other",
            title="Submission confirmed",
            message="The registration was submitted.",
        )
        self.client.force_login(self.user_a)

        inbox = self.client.get("/api/v1/notifications")
        first_read = self.client.post(f"/api/v1/notifications/{own.pk}/read")
        second_read = self.client.post(f"/api/v1/notifications/{own.pk}/read")
        hidden = self.client.post(f"/api/v1/notifications/{other.pk}/read")

        self.assertEqual(inbox.status_code, 200, inbox.content)
        self.assertEqual(inbox.json()["total"], 1)
        self.assertEqual(inbox.json()["unread_count"], 1)
        self.assertEqual(inbox.json()["items"][0]["registration_id"], self.registration_a.pk)
        self.assertEqual(first_read.status_code, 200, first_read.content)
        self.assertEqual(second_read.status_code, 200, second_read.content)
        self.assertTrue(first_read.json()["is_read"])
        self.assertEqual(hidden.status_code, 404)

    def test_create_snapshots_list_price_and_opens_category_review(self):
        self.set_price("125.00")
        self.client.force_login(self.user_a)

        response = self.client.post(
            "/api/v1/registrations",
            data=json.dumps(self.payload()),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201, response.content)
        registration = Registration.objects.get(project_title="TEST opportunity")
        item = registration.items.get()
        self.assertEqual(str(item.list_unit_price_snapshot), "125.00")
        self.assertEqual(str(item.requested_discount_percent), "99.20")
        approval = registration.category_approvals.get()
        self.assertEqual(approval.category, self.product.category)
        self.assertEqual(approval.status, RegistrationCategoryApproval.Status.PENDING)

    def test_admin_can_approve_category_prices_with_expiry(self):
        self.set_price("125.00")
        self.client.force_login(self.user_a)
        created = self.client.post(
            "/api/v1/registrations",
            data=json.dumps(self.payload()),
            content_type="application/json",
        )
        registration = Registration.objects.get(pk=created.json()["id"])
        approval = registration.category_approvals.get()
        item = registration.items.get()
        self.client.force_login(self.admin)

        response = self.client.post(
            f"/api/v1/review/category-approvals/{approval.pk}/decision",
            data=json.dumps(
                {
                    "version": approval.version,
                    "status": "approved",
                    "rationale": "Pricing is commercially acceptable.",
                    "valid_until": (date.today() + timedelta(days=30)).isoformat(),
                    "approved_prices": {str(item.pk): "95.00"},
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        approval.refresh_from_db()
        self.assertEqual(approval.status, RegistrationCategoryApproval.Status.APPROVED)
        self.assertEqual(
            RegistrationItemApproval.objects.get(registration_item=item).approved_unit_price,
            95,
        )
        self.assertTrue(registration.events.filter(event_type="Commercial decision").exists())
        notice = RegistrationNotification.objects.get(
            recipient=self.user_a,
            registration=registration,
            event_type=RegistrationNotification.EventType.PRICE_DECISION,
        )
        self.assertEqual(notice.title, "Price request approved")
        self.assertNotIn("95", notice.message)

    def test_company_cannot_make_a_commercial_decision(self):
        approval = RegistrationCategoryApproval.objects.create(
            registration=self.registration_a, category=self.product.category
        )
        self.client.force_login(self.user_a)

        response = self.client.post(
            f"/api/v1/review/category-approvals/{approval.pk}/decision",
            data=json.dumps(
                {
                    "version": approval.version,
                    "status": "rejected",
                    "rationale": "Company users cannot decide pricing.",
                    "approved_prices": {},
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_approved_renewal_adds_thirty_days_to_current_expiry(self):
        current_expiry = date.today() + timedelta(days=10)
        approval = RegistrationCategoryApproval.objects.create(
            registration=self.registration_a,
            category=self.product.category,
            status=RegistrationCategoryApproval.Status.APPROVED,
            valid_until=current_expiry,
        )
        renewal = PriceApprovalRenewal.objects.create(
            category_approval=approval,
            requested_by=self.user_a,
            reason="The procurement schedule moved.",
            previous_valid_until=current_expiry,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            f"/api/v1/review/renewals/{renewal.pk}/decision",
            data=json.dumps({"approve": True, "reason": "Schedule evidence is sufficient."}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        approval.refresh_from_db()
        renewal.refresh_from_db()
        self.assertEqual(approval.valid_until, current_expiry + timedelta(days=30))
        self.assertEqual(renewal.new_valid_until, approval.valid_until)

    def test_create_rejects_missing_children_and_evidence_confirmation(self):
        self.client.force_login(self.user_a)
        response = self.client.post(
            "/api/v1/registrations",
            data=json.dumps(
                self.payload(
                    competitor_items=[],
                    items=[],
                    evidence_sharing_confirmed=False,
                )
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "validation_error")

    def test_update_is_audited_and_increments_version(self):
        self.client.force_login(self.user_a)
        response = self.client.put(
            f"/api/v1/registrations/{self.registration_a.pk}",
            data=json.dumps(
                self.payload(
                    version=self.registration_a.version,
                    project_title="Edited project",
                )
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.registration_a.refresh_from_db()
        self.assertEqual(self.registration_a.version, 2)
        self.assertTrue(self.registration_a.needs_review)
        event = RegistrationEvent.objects.get(registration=self.registration_a)
        self.assertEqual(event.snapshot["project_title"], "Company A secret project")
        detail = self.client.get(f"/api/v1/registrations/{self.registration_a.pk}")
        self.assertEqual(detail.status_code, 200, detail.content)
        event_payload = detail.json()["events"][0]
        project_change = next(
            change for change in event_payload["changes"] if change["label"] == "Project title"
        )
        self.assertEqual(project_change["previous"], "Company A secret project")
        self.assertEqual(project_change["current"], "Edited project")

    def test_update_rejects_stale_version(self):
        self.client.force_login(self.user_a)
        response = self.client.put(
            f"/api/v1/registrations/{self.registration_a.pk}",
            data=json.dumps(self.payload(version=99)),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "edit_conflict")

    def test_company_user_cannot_use_review_endpoints(self):
        self.client.force_login(self.user_a)

        scopes = self.client.get("/api/v1/review/opportunity-scopes")
        decision = self.client.post(
            f"/api/v1/review/registrations/{self.registration_a.pk}/decision",
            data=json.dumps(
                {
                    "version": self.registration_a.version,
                    "decision": "start_review",
                    "rationale": "Reviewing the submitted evidence.",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(scopes.status_code, 403)
        self.assertEqual(decision.status_code, 403)

    def test_admin_review_lifecycle_creates_opportunity_and_audit_decisions(self):
        self.client.force_login(self.admin)

        started = self.client.post(
            f"/api/v1/review/registrations/{self.registration_a.pk}/decision",
            data=json.dumps(
                {
                    "version": self.registration_a.version,
                    "decision": "start_review",
                    "rationale": "Evidence review has started.",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(started.status_code, 200, started.content)
        self.assertEqual(started.json()["status"], Registration.Status.UNDER_REVIEW)
        self.assertIsNone(started.json()["opportunity_scope_id"])
        self.assertEqual(Opportunity.objects.count(), 0)

        confirmed = self.client.post(
            f"/api/v1/review/registrations/{self.registration_a.pk}/decision",
            data=json.dumps(
                {
                    "version": started.json()["version"],
                    "decision": "confirm_match",
                    "rationale": "Specific evidence supports a distinct whole opportunity.",
                    "create_new_opportunity": True,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(confirmed.status_code, 200, confirmed.content)
        self.registration_a.refresh_from_db()
        self.assertEqual(self.registration_a.status, Registration.Status.ELIGIBLE_MATCHED)
        self.assertIsNotNone(self.registration_a.opportunity_scope_id)
        self.assertEqual(Opportunity.objects.count(), 1)
        self.assertEqual(
            RegistrationReviewDecision.objects.filter(registration=self.registration_a).count(),
            2,
        )
        notice = RegistrationNotification.objects.get(
            recipient=self.user_a,
            registration=self.registration_a,
            event_type=RegistrationNotification.EventType.REGISTRATION_DECISION,
        )
        self.assertEqual(notice.title, "Registration confirmed")

    def test_company_detail_hides_internal_matching_review_information(self):
        RegistrationEvent.objects.create(
            registration=self.registration_a,
            actor=self.admin,
            event_type="Start review",
            details="Internal intake assessment must remain private.",
        )
        RegistrationEvent.objects.create(
            registration=self.registration_a,
            actor=self.admin,
            event_type="Confirm eligible match",
            details="Internal override reasoning must remain private.",
        )
        RegistrationEvent.objects.create(
            registration=self.registration_a,
            actor=self.admin,
            event_type="Request changes",
            details="Upload the missing procurement notice.",
        )
        self.client.force_login(self.user_a)

        response = self.client.get(f"/api/v1/registrations/{self.registration_a.pk}")

        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        self.assertIsNone(payload["matching_suggestion"])
        self.assertNotIn("Start review", {event["event_type"] for event in payload["events"]})
        self.assertNotContains(response, "Internal intake assessment")
        self.assertNotContains(response, "Internal override reasoning")
        confirmed = next(
            event for event in payload["events"] if event["event_type"] == "Confirm eligible match"
        )
        self.assertEqual(
            confirmed["details"],
            "DBGI confirmed this registration's opportunity match.",
        )
        requested = next(
            event for event in payload["events"] if event["event_type"] == "Request changes"
        )
        self.assertEqual(requested["details"], "Upload the missing procurement notice.")

    def test_admin_review_rejects_stale_version_and_invalid_transition(self):
        self.client.force_login(self.admin)
        url = f"/api/v1/review/registrations/{self.registration_a.pk}/decision"

        stale = self.client.post(
            url,
            data=json.dumps(
                {
                    "version": 999,
                    "decision": "start_review",
                    "rationale": "This version is stale.",
                }
            ),
            content_type="application/json",
        )
        invalid = self.client.post(
            url,
            data=json.dumps(
                {
                    "version": self.registration_a.version,
                    "decision": "confirm_match",
                    "rationale": "Cannot confirm before review starts.",
                    "create_new_opportunity": True,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(stale.status_code, 409)
        self.assertEqual(invalid.status_code, 400)

    def test_initial_products_are_seeded_without_prices(self):
        printers = Product.objects.filter(code__in=("M1820W", "P1820W"))
        self.assertEqual(set(printers.values_list("code", flat=True)), {"M1820W", "P1820W"})

    def test_attachment_upload_download_delete_and_scope(self):
        self.client.force_login(self.user_a)
        version = self.registration_a.version
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            upload = self.client.post(
                f"/api/v1/registrations/{self.registration_a.pk}/attachments"
                f"?description=Support&version={version}",
                data={"file": SimpleUploadedFile("support.pdf", b"%PDF-1.4 valid evidence")},
            )
            self.assertEqual(upload.status_code, 201, upload.content)
            attachment_id = upload.json()["id"]
            self.assertEqual(
                self.registration_a.events.filter(event_type="Attachment added").count(), 1
            )

            download = self.client.get(reverse("registration-attachment", args=[attachment_id]))
            self.assertEqual(download.status_code, 200)
            self.assertEqual(download["Cache-Control"], "private, no-store")
            self.assertEqual(b"".join(download.streaming_content), b"%PDF-1.4 valid evidence")

            self.client.force_login(self.user_b)
            hidden = self.client.get(reverse("registration-attachment", args=[attachment_id]))
            self.assertEqual(hidden.status_code, 404)

            self.client.force_login(self.user_a)
            with self.captureOnCommitCallbacks(execute=True):
                deleted = self.client.delete(
                    f"/api/v1/attachments/{attachment_id}?version={version}"
                )
            self.assertEqual(deleted.status_code, 204)
            self.assertFalse(RegistrationAttachment.objects.filter(pk=attachment_id).exists())
            self.assertEqual(
                self.registration_a.events.filter(event_type="Attachment removed").count(), 1
            )

    def test_attachment_changes_are_locked_after_review_starts(self):
        self.client.force_login(self.user_a)
        version = self.registration_a.version
        self.registration_a.status = Registration.Status.UNDER_REVIEW
        self.registration_a.save(update_fields=["status"])
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                f"/api/v1/registrations/{self.registration_a.pk}/attachments?version={version}",
                data={"file": SimpleUploadedFile("support.pdf", b"%PDF-1.4 evidence")},
            )
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(response.json()["code"], "evidence_locked")
        self.assertFalse(RegistrationAttachment.objects.exists())

    def test_attachment_changes_reject_a_stale_version(self):
        self.client.force_login(self.user_a)
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                f"/api/v1/registrations/{self.registration_a.pk}/attachments?version=99",
                data={"file": SimpleUploadedFile("support.pdf", b"%PDF-1.4 evidence")},
            )
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(response.json()["code"], "edit_conflict")

    def test_attachment_validation_rejects_extension_and_size(self):
        bad_extension = RegistrationAttachment(
            registration=self.registration_a,
            file=SimpleUploadedFile("evidence.exe", b"invalid"),
            original_name="evidence.exe",
            uploaded_by=self.user_a,
        )
        oversized = RegistrationAttachment(
            registration=self.registration_a,
            file=SimpleUploadedFile("large.pdf", b"x" * (10 * 1024 * 1024 + 1)),
            original_name="large.pdf",
            uploaded_by=self.user_a,
        )
        with self.assertRaises(ValidationError):
            bad_extension.full_clean()
        with self.assertRaises(ValidationError):
            oversized.full_clean()

    def test_attachment_validation_rejects_a_renamed_file(self):
        renamed = RegistrationAttachment(
            registration=self.registration_a,
            file=SimpleUploadedFile("evidence.pdf", b"MZ\x90\x00 not a pdf"),
            original_name="evidence.pdf",
            uploaded_by=self.user_a,
        )
        with self.assertRaises(ValidationError):
            renamed.full_clean()

    def test_cannot_upload_attachment_to_other_company(self):
        self.client.force_login(self.user_a)
        response = self.client.post(
            f"/api/v1/registrations/{self.registration_b.pk}/attachments"
            f"?version={self.registration_b.version}",
            data={"file": SimpleUploadedFile("support.pdf", b"%PDF-1.4 evidence")},
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_edit_bumps_the_version_and_keeps_the_prior_snapshot(self):
        registration_admin = RegistrationAdmin(Registration, AdminSite())
        request = RequestFactory().post("/admin/registrations/registration/")
        request.user = self.admin
        obj = Registration.objects.get(pk=self.registration_a.pk)
        obj.project_title = "Admin edited title"

        registration_admin.save_model(request, obj, SimpleNamespace(), change=True)

        obj.refresh_from_db()
        self.assertEqual(obj.version, self.registration_a.version + 1)
        self.assertEqual(
            request.registration_prior_snapshot["project_title"], self.registration_a.project_title
        )

    def test_change_summary_names_fields_and_collections(self):
        changes = registration_change_summary(
            {
                "project_title": "Original title",
                "status": "submitted",
                "items": [{"quantity": 1}],
            },
            {
                "project_title": "Revised title",
                "status": "under_review",
                "items": [{"quantity": 2}],
            },
        )

        self.assertEqual(
            changes,
            [
                "Project title: Original title to Revised title",
                "Registration status: submitted to under review",
                "Requested products: updated",
            ],
        )

    def test_admin_inline_edit_records_before_and_resulting_snapshots(self):
        registration_admin = RegistrationAdmin(Registration, AdminSite())
        request = RequestFactory().post("/admin/registrations/registration/")
        request.user = self.admin
        obj = Registration.objects.get(pk=self.registration_a.pk)
        item = obj.items.get()

        registration_admin.save_model(request, obj, SimpleNamespace(), change=True)

        def save_inline(*args, **kwargs):
            item.quantity = 7
            item.save(update_fields=["quantity"])

        form = SimpleNamespace(instance=obj, save_m2m=lambda: None)
        with patch.object(registration_admin, "save_formset", side_effect=save_inline):
            registration_admin.save_related(request, form, [object()], change=True)

        event = obj.events.get(event_type="Admin update")
        self.assertEqual(event.snapshot["items"][0]["quantity"], 2)
        self.assertEqual(event.resulting_snapshot["items"][0]["quantity"], 7)
        self.assertEqual(event.snapshot["version"], 1)
        self.assertEqual(event.resulting_snapshot["version"], 2)

    def test_admin_status_decision_notifies_company_users(self):
        registration_admin = RegistrationAdmin(Registration, AdminSite())
        request = RequestFactory().post("/admin/registrations/registration/")
        request.user = self.admin
        obj = Registration.objects.get(pk=self.registration_a.pk)
        obj.status = Registration.Status.REJECTED

        registration_admin.save_model(request, obj, SimpleNamespace(), change=True)
        form = SimpleNamespace(instance=obj, save_m2m=lambda: None)
        registration_admin.save_related(request, form, [], change=True)

        notice = RegistrationNotification.objects.get(
            recipient=self.user_a,
            registration=obj,
            event_type=RegistrationNotification.EventType.REGISTRATION_DECISION,
        )
        self.assertEqual(notice.title, "Registration rejected")

    @override_settings(DEBUG=False)
    def test_clearing_transactional_records_requires_debug(self):
        from devtools.scenarios import clear_transactional_records

        with self.assertRaises(CommandError):
            clear_transactional_records()
        self.assertTrue(Registration.objects.filter(pk=self.registration_a.pk).exists())

    def test_finalize_bumps_the_version_and_rejects_a_stale_one(self):
        self.client.force_login(self.user_a)
        version = self.registration_a.version

        response = self.client.post(
            f"/api/v1/registrations/{self.registration_a.pk}/finalize",
            data=json.dumps({"version": version}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["version"], version + 1)
        self.registration_a.refresh_from_db()
        # Not confirmed yet, so DBGI sees the files when it reviews; no separate alert
        self.assertFalse(self.registration_a.needs_review)
        self.assertTrue(
            self.registration_a.events.filter(event_type="Attachments submitted").exists()
        )

        stale = self.client.post(
            f"/api/v1/registrations/{self.registration_a.pk}/finalize",
            data=json.dumps({"version": version}),
            content_type="application/json",
        )
        self.assertEqual(stale.status_code, 409, stale.content)
        self.assertEqual(stale.json()["code"], "edit_conflict")

    def withdraw(self, registration, reason="The end-user cancelled this purchase.", version=None):
        return self.client.post(
            f"/api/v1/registrations/{registration.pk}/withdraw",
            data=json.dumps(
                {"version": registration.version if version is None else version, "reason": reason}
            ),
            content_type="application/json",
        )

    def test_company_withdraws_own_registration_and_dbgi_is_notified(self):
        self.client.force_login(self.user_a)
        response = self.withdraw(self.registration_a)

        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(body["status"], Registration.Status.WITHDRAWN)
        self.assertFalse(body["can_edit"])
        self.assertFalse(body["can_withdraw"])
        self.registration_a.refresh_from_db()
        self.assertIsNotNone(self.registration_a.withdrawn_at)
        event = self.registration_a.events.get(event_type="Withdrawn")
        self.assertEqual(event.actor, self.user_a)
        self.assertEqual(event.details, "The end-user cancelled this purchase.")
        notification = RegistrationNotification.objects.get(
            event_type=RegistrationNotification.EventType.REGISTRATION_WITHDRAWN
        )
        self.assertEqual(notification.recipient, self.admin)
        self.assertIn("The end-user cancelled this purchase.", notification.message)
        self.assertEqual(
            notification.email_status, RegistrationNotification.EmailStatus.NOT_REQUESTED
        )
        self.assertEqual(mail.outbox, [])

    def test_only_the_owning_company_can_withdraw(self):
        self.client.force_login(self.user_b)
        self.assertEqual(self.withdraw(self.registration_a).status_code, 404)
        self.client.force_login(self.admin)
        self.assertEqual(self.withdraw(self.registration_a).status_code, 403)
        self.registration_a.refresh_from_db()
        self.assertNotEqual(self.registration_a.status, Registration.Status.WITHDRAWN)

    def test_withdrawal_needs_a_reason_and_the_current_version(self):
        self.client.force_login(self.user_a)
        short = self.withdraw(self.registration_a, reason="   no ")
        self.assertEqual(short.status_code, 400, short.content)
        stale = self.withdraw(self.registration_a, version=self.registration_a.version - 1)
        self.assertEqual(stale.status_code, 409, stale.content)
        self.assertEqual(stale.json()["code"], "edit_conflict")

    def test_rejected_registration_cannot_be_withdrawn(self):
        Registration.objects.filter(pk=self.registration_a.pk).update(
            status=Registration.Status.REJECTED
        )
        self.registration_a.refresh_from_db()
        self.client.force_login(self.user_a)
        response = self.withdraw(self.registration_a)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(response.json()["code"], "invalid_transition")

    def test_withdrawn_registration_is_final_and_leaves_the_ranking(self):
        opportunity = Opportunity.objects.create(
            title="Shared opportunity",
            end_user=self.end_user,
            end_user_name=self.end_user.official_name,
            end_user_address="Test address",
            created_by=self.admin,
        )
        scope = OpportunityScope.objects.create(
            opportunity=opportunity,
            name="Whole opportunity",
            scope_type=OpportunityScope.ScopeType.WHOLE,
        )
        Registration.objects.filter(pk__in=[self.registration_a.pk, self.registration_b.pk]).update(
            status=Registration.Status.ELIGIBLE_MATCHED, opportunity_scope=scope
        )
        self.registration_a.refresh_from_db()

        self.client.force_login(self.user_a)
        self.assertEqual(self.withdraw(self.registration_a).status_code, 200)
        self.registration_a.refresh_from_db()

        edit = self.client.put(
            f"/api/v1/registrations/{self.registration_a.pk}",
            data=json.dumps({**self.payload(), "version": self.registration_a.version}),
            content_type="application/json",
        )
        self.assertEqual(edit.status_code, 409, edit.content)
        self.assertEqual(edit.json()["code"], "registration_withdrawn")
        again = self.withdraw(self.registration_a)
        self.assertEqual(again.json()["code"], "invalid_transition")

        self.client.force_login(self.admin)
        rankings = self.client.get("/api/v1/rankings").json()
        ranked = [
            entry["registration_id"] for item in rankings["items"] for entry in item["entries"]
        ]
        self.assertNotIn(self.registration_a.pk, ranked)
        self.assertIn(self.registration_b.pk, ranked)

    def link_to_project(self, *registrations):
        opportunity = Opportunity.objects.create(
            title="Outcome opportunity",
            end_user=self.end_user,
            end_user_name=self.end_user.official_name,
            end_user_address="Test address",
            created_by=self.admin,
        )
        scope = OpportunityScope.objects.create(
            opportunity=opportunity,
            name="Whole opportunity",
            scope_type=OpportunityScope.ScopeType.WHOLE,
        )
        Registration.objects.filter(pk__in=[r.pk for r in registrations]).update(
            status=Registration.Status.ELIGIBLE_MATCHED, opportunity_scope=scope
        )
        for registration in registrations:
            registration.refresh_from_db()
        return opportunity

    def report_outcome(self, registration, outcome="won", note="We received the notice of award."):
        return self.client.post(
            f"/api/v1/registrations/{registration.pk}/outcome-reports",
            data=json.dumps({"outcome": outcome, "note": note}),
            content_type="application/json",
        )

    def decide_outcome(self, report, confirm=True, note="Checked the notice of award."):
        return self.client.post(
            f"/api/v1/review/outcome-reports/{report.pk}/decision",
            data=json.dumps({"confirm": confirm, "note": note}),
            content_type="application/json",
        )

    def test_partner_reports_outcome_and_dbgi_is_notified(self):
        self.link_to_project(self.registration_a)
        self.client.force_login(self.user_a)

        response = self.report_outcome(self.registration_a)

        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertFalse(body["can_report_outcome"])
        self.assertEqual(body["outcome_reports"][0]["outcome"], "won")
        self.assertEqual(body["outcome_reports"][0]["status"], "pending")
        notice = RegistrationNotification.objects.get(
            event_type=RegistrationNotification.EventType.OUTCOME_REPORTED
        )
        self.assertEqual(notice.recipient, self.admin)
        self.assertEqual(notice.email_status, RegistrationNotification.EmailStatus.PENDING)
        second = self.report_outcome(self.registration_a, outcome="lost")
        self.assertEqual(second.status_code, 409, second.content)
        self.assertEqual(second.json()["code"], "outcome_report_pending")

    def test_only_a_linked_registration_can_report_an_outcome(self):
        self.client.force_login(self.user_a)
        unlinked = self.report_outcome(self.registration_a)
        self.assertEqual(unlinked.status_code, 400, unlinked.content)
        detail = self.client.get(f"/api/v1/registrations/{self.registration_a.pk}").json()
        self.assertFalse(detail["can_report_outcome"])
        self.link_to_project(self.registration_a)
        self.client.force_login(self.user_b)
        self.assertEqual(self.report_outcome(self.registration_a).status_code, 404)
        self.client.force_login(self.admin)
        self.assertEqual(self.report_outcome(self.registration_a).status_code, 403)

    def test_dbgi_confirms_outcome_for_every_linked_registration(self):
        opportunity = self.link_to_project(self.registration_a, self.registration_b)
        self.client.force_login(self.user_a)
        self.report_outcome(self.registration_a)
        report = ProjectOutcomeReport.objects.get()

        self.client.force_login(self.user_a)
        self.assertEqual(self.decide_outcome(report).status_code, 403)
        self.client.force_login(self.admin)
        response = self.decide_outcome(report)

        self.assertEqual(response.status_code, 200, response.content)
        opportunity.refresh_from_db()
        self.assertEqual(opportunity.project_status, Opportunity.ProjectStatus.WON)
        report.refresh_from_db()
        self.assertEqual(report.status, ProjectOutcomeReport.Status.CONFIRMED)
        self.assertEqual(report.decided_by, self.admin)
        for registration in (self.registration_a, self.registration_b):
            self.assertTrue(
                registration.events.filter(event_type="Project status changed").exists()
            )
        self.assertTrue(
            RegistrationNotification.objects.filter(
                recipient=self.user_a, event_key=f"outcome-report:{report.pk}:confirmed"
            ).exists()
        )
        again = self.decide_outcome(report)
        self.assertEqual(again.json()["code"], "invalid_transition")
        self.client.force_login(self.user_a)
        closed = self.report_outcome(self.registration_a, outcome="lost")
        self.assertEqual(closed.status_code, 400, closed.content)

    def test_declined_outcome_keeps_the_project_status(self):
        opportunity = self.link_to_project(self.registration_a)
        self.client.force_login(self.user_a)
        self.report_outcome(self.registration_a, outcome="cancelled")
        report = ProjectOutcomeReport.objects.get()

        self.client.force_login(self.admin)
        response = self.decide_outcome(report, confirm=False, note="The agency has not cancelled.")

        self.assertEqual(response.status_code, 200, response.content)
        opportunity.refresh_from_db()
        self.assertEqual(opportunity.project_status, Opportunity.ProjectStatus.UPCOMING)
        report.refresh_from_db()
        self.assertEqual(report.status, ProjectOutcomeReport.Status.REJECTED)
        self.assertEqual(report.decision_note, "The agency has not cancelled.")
        self.client.force_login(self.user_a)
        detail = self.client.get(f"/api/v1/registrations/{self.registration_a.pk}").json()
        self.assertTrue(detail["can_report_outcome"])

    def test_unconfirmed_registration_gets_reminder_then_dbgi_review(self):
        # Both test registrations are unconfirmed; count from the later submission
        submitted = max(
            self.registration_a.original_submitted_at, self.registration_b.original_submitted_at
        )

        early = process_deadlines(now=submitted + timedelta(days=52))
        self.assertEqual(early.reminders, 0)
        reminder = process_deadlines(now=submitted + timedelta(days=53))
        self.assertEqual(reminder.reminders, 2)
        self.assertTrue(
            RegistrationNotification.objects.filter(
                recipient=self.user_a,
                event_type=RegistrationNotification.EventType.DEADLINE_REMINDER,
            ).exists()
        )
        self.assertEqual(process_deadlines(now=submitted + timedelta(days=54)).reminders, 0)

        limit = process_deadlines(now=submitted + timedelta(days=60))
        self.assertEqual(limit.limits_reached, 2)
        self.registration_a.refresh_from_db()
        self.assertTrue(self.registration_a.needs_review)
        self.assertEqual(self.registration_a.status, Registration.Status.SUBMITTED)
        self.assertTrue(
            self.registration_a.events.filter(event_type="60-day limit reached").exists()
        )
        self.assertTrue(
            RegistrationNotification.objects.filter(
                recipient=self.admin,
                event_type=RegistrationNotification.EventType.DEADLINE_REACHED,
            ).exists()
        )
        again = process_deadlines(now=submitted + timedelta(days=61))
        self.assertEqual((again.reminders, again.limits_reached), (0, 0))

    def test_confirmed_registration_has_no_confirmation_deadline(self):
        self.link_to_project(self.registration_a, self.registration_b)
        summary = process_deadlines(
            now=self.registration_a.original_submitted_at + timedelta(days=90)
        )
        self.assertEqual((summary.reminders, summary.limits_reached), (0, 0))

    def test_project_on_hold_keeps_places_for_sixty_days(self):
        opportunity = self.link_to_project(self.registration_a)
        self.client.force_login(self.admin)
        response = self.client.post(
            f"/api/v1/review/opportunities/{opportunity.pk}/project-status",
            data=json.dumps({"status": "on_hold", "reason": "The agency postponed the bid."}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        opportunity.refresh_from_db()
        self.assertIsNotNone(opportunity.on_hold_since)
        since = opportunity.on_hold_since

        self.assertEqual(process_deadlines(now=since + timedelta(days=53)).hold_reminders, 1)
        self.assertTrue(
            RegistrationNotification.objects.filter(
                recipient=self.user_a,
                event_type=RegistrationNotification.EventType.DEADLINE_REMINDER,
            ).exists()
        )
        self.assertEqual(process_deadlines(now=since + timedelta(days=60)).hold_limits_reached, 1)
        self.registration_a.refresh_from_db()
        self.assertTrue(self.registration_a.needs_review)
        self.assertTrue(
            self.registration_a.events.filter(event_type="60-day hold limit reached").exists()
        )
        self.assertEqual(process_deadlines(now=since + timedelta(days=61)).hold_limits_reached, 0)

        self.client.post(
            f"/api/v1/review/opportunities/{opportunity.pk}/project-status",
            data=json.dumps({"status": "active", "reason": "The bid was reposted."}),
            content_type="application/json",
        )
        opportunity.refresh_from_db()
        self.assertIsNone(opportunity.on_hold_since)

    def test_only_the_submitter_is_emailed_but_the_whole_company_is_notified(self):
        NotificationEventSetting.objects.update_or_create(
            event_type=RegistrationNotification.EventType.SUBMISSION_CONFIRMED,
            defaults={"email_enabled": True},
        )
        colleague = User.objects.create_user(
            username="dealer-a-colleague",
            email="colleague@example.invalid",
            password="example-password",
            company=self.company_a,
        )
        self.client.force_login(self.user_a)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                "/api/v1/registrations",
                data=json.dumps(self.payload()),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 201, response.content)
        notices = RegistrationNotification.objects.filter(
            registration_id=response.json()["id"],
            event_type=RegistrationNotification.EventType.SUBMISSION_CONFIRMED,
        )
        self.assertEqual(
            notices.get(recipient=self.user_a).email_status,
            RegistrationNotification.EmailStatus.SENT,
        )
        self.assertEqual(
            notices.get(recipient=colleague).email_status,
            RegistrationNotification.EmailStatus.NOT_REQUESTED,
        )
        self.assertFalse([m for m in mail.outbox if colleague.email in m.to])

    def test_dbgi_is_emailed_when_a_registration_needs_review(self):
        self.client.force_login(self.user_a)
        with self.captureOnCommitCallbacks(execute=True):
            created = self.client.post(
                "/api/v1/registrations",
                data=json.dumps(self.payload()),
                content_type="application/json",
            )
        self.assertEqual(created.status_code, 201, created.content)
        notice = RegistrationNotification.objects.get(
            registration_id=created.json()["id"],
            recipient=self.admin,
            event_type=RegistrationNotification.EventType.REVIEW_NEEDED,
        )
        self.assertEqual(notice.email_status, RegistrationNotification.EmailStatus.SENT)
        self.assertIn(self.admin.email, [address for m in mail.outbox for address in m.to])

        Registration.objects.filter(pk=self.registration_a.pk).update(
            status=Registration.Status.CHANGES_REQUESTED
        )
        self.registration_a.refresh_from_db()
        edit = self.client.put(
            f"/api/v1/registrations/{self.registration_a.pk}",
            data=json.dumps({**self.payload(), "version": self.registration_a.version}),
            content_type="application/json",
        )
        self.assertEqual(edit.status_code, 200, edit.content)
        self.assertTrue(
            RegistrationNotification.objects.filter(
                registration=self.registration_a,
                recipient=self.admin,
                event_type=RegistrationNotification.EventType.REVIEW_NEEDED,
                title="Review needed: corrections submitted",
            ).exists()
        )

    def test_withdrawal_notice_to_dbgi_is_not_emailed(self):
        self.client.force_login(self.user_a)
        self.assertEqual(self.withdraw(self.registration_a).status_code, 200)
        notice = RegistrationNotification.objects.get(
            recipient=self.admin,
            event_type=RegistrationNotification.EventType.REGISTRATION_WITHDRAWN,
        )
        self.assertEqual(notice.email_status, RegistrationNotification.EmailStatus.NOT_REQUESTED)

    def test_company_is_reminded_14_days_before_an_approved_price_expires(self):
        approval = RegistrationCategoryApproval.objects.create(
            registration=self.registration_a,
            category="Test category",
            status=RegistrationCategoryApproval.Status.APPROVED,
            valid_until=date(2026, 12, 31),
        )
        early = process_deadlines(now=timezone.make_aware(datetime(2026, 12, 16, 9)))
        self.assertEqual(early.price_reminders, 0)
        due = process_deadlines(now=timezone.make_aware(datetime(2026, 12, 17, 9)))
        self.assertEqual(due.price_reminders, 1)
        self.assertTrue(
            RegistrationNotification.objects.filter(
                recipient=self.user_a,
                event_key__startswith=f"approval:{approval.pk}:expiry-reminder",
            ).exists()
        )
        again = process_deadlines(now=timezone.make_aware(datetime(2026, 12, 18, 9)))
        self.assertEqual(again.price_reminders, 0)

    def set_price(self, amount, **fields):
        return ProductPrice.objects.create(
            product=self.product, unit_price=amount, reason="Test price", **fields
        )

    def register_deal(self):
        self.client.force_login(self.user_a)
        response = self.client.post(
            "/api/v1/registrations",
            data=json.dumps(self.payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        return Registration.objects.get(pk=response.json()["id"])

    def test_new_price_never_changes_an_earlier_registration(self):
        old_price = self.set_price("100.00")
        earlier = self.register_deal()
        new_price = self.set_price("150.00")
        later = self.register_deal()

        earlier_item = earlier.items.get()
        self.assertEqual(str(earlier_item.list_unit_price_snapshot), "100.00")
        self.assertEqual(earlier_item.price_version, old_price)
        later_item = later.items.get()
        self.assertEqual(str(later_item.list_unit_price_snapshot), "150.00")
        self.assertEqual(later_item.price_version, new_price)
        self.assertEqual(new_price.vat_basis, ProductPrice.VatBasis.INCLUSIVE)
        self.assertEqual(new_price.currency, self.product.currency)

    def test_future_price_waits_for_its_start_date(self):
        current = self.set_price("100.00")
        self.set_price("150.00", effective_from=timezone.now() + timedelta(days=7))

        self.client.force_login(self.user_a)
        options = self.client.get("/api/v1/products").json()
        option = next(o for o in options if o["id"] == self.product.pk)
        self.assertEqual(Decimal(option["list_price"]), Decimal("100.00"))
        self.assertEqual(self.register_deal().items.get().price_version, current)
        later = Product.objects.with_list_price(at=timezone.now() + timedelta(days=8)).get(
            pk=self.product.pk
        )
        self.assertEqual(later.list_price, Decimal("150.00"))

    def test_product_without_a_price_shows_zero(self):
        product = Product.objects.with_list_price().get(pk=self.product.pk)
        self.assertEqual(product.list_price, Decimal("0.00"))
        item = self.register_deal().items.get()
        self.assertEqual(str(item.list_unit_price_snapshot), "0.00")
        self.assertIsNone(item.price_version)

    def test_saved_price_cannot_change_and_cannot_start_in_the_past(self):
        price = self.set_price("100.00")
        price.unit_price = "1.00"
        with self.assertRaises(ValidationError):
            price.save()
        past = ProductPrice(
            product=self.product,
            unit_price="90.00",
            reason="Backdated",
            effective_from=timezone.now() - timedelta(days=2),
        )
        with self.assertRaises(ValidationError):
            past.full_clean()
        self.set_price("120.00", effective_from=timezone.now() + timedelta(days=1)).full_clean()

    def test_admin_adds_a_price_and_records_who_set_it(self):
        self.client.force_login(self.admin)
        url = reverse("admin:registrations_product_change", args=[self.product.pk])
        start = timezone.localtime() + timedelta(days=1)
        response = self.client.post(
            url,
            {
                "code": self.product.code,
                "name": self.product.name,
                "category": self.product.category,
                "currency": self.product.currency,
                "is_active": "on",
                "prices-TOTAL_FORMS": "1",
                "prices-INITIAL_FORMS": "0",
                "prices-MIN_NUM_FORMS": "0",
                "prices-MAX_NUM_FORMS": "1000",
                "prices-0-unit_price": "130.00",
                "prices-0-effective_from_0": start.strftime("%Y-%m-%d"),
                "prices-0-effective_from_1": start.strftime("%H:%M:%S"),
                "prices-0-reason": "Supplier increase",
            },
        )
        self.assertEqual(response.status_code, 302, response.content[:2000])
        price = ProductPrice.objects.get(product=self.product)
        self.assertEqual(price.created_by, self.admin)
        self.assertEqual(str(price.unit_price), "130.00")
        self.assertEqual(self.client.get(url).status_code, 200)

    def edit_deal(self, registration, **changes):
        registration.refresh_from_db()
        item = registration.items.get()
        payload = {
            **self.payload(),
            "project_title": registration.project_title,
            "contact_person": registration.contact_person,
            "items": [
                {
                    "product_id": item.product_id,
                    "non_catalog_name": item.non_catalog_name,
                    "quantity": item.quantity,
                    "requested_unit_price": str(item.requested_unit_price),
                    "justification": item.justification,
                }
            ],
            "version": registration.version,
            **changes,
        }
        return self.client.put(
            f"/api/v1/registrations/{registration.pk}",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def registered_deal(self):
        self.set_price("100.00")
        registration = self.register_deal()
        Registration.objects.filter(pk=registration.pk).update(
            status=Registration.Status.ELIGIBLE_MATCHED, needs_review=False
        )
        self.set_price("150.00")
        return registration

    def test_administrative_correction_keeps_price_status_and_needs_no_review(self):
        registration = self.registered_deal()
        response = self.edit_deal(registration, contact_person="Corrected Name")

        self.assertEqual(response.status_code, 200, response.content)
        registration.refresh_from_db()
        self.assertEqual(registration.contact_person, "Corrected Name")
        self.assertEqual(registration.status, Registration.Status.ELIGIBLE_MATCHED)
        self.assertFalse(registration.needs_review)
        item = registration.items.get()
        self.assertEqual(str(item.list_unit_price_snapshot), "100.00")
        self.assertEqual(item.price_basis, RegistrationItem.PriceBasis.ORIGINAL)
        self.assertTrue(registration.events.filter(event_type="Administrative correction").exists())

    def test_formatting_only_title_change_is_administrative(self):
        registration = self.registered_deal()
        Registration.objects.filter(pk=registration.pk).update(
            project_title="Printers for City Hall"
        )
        registration.refresh_from_db()
        self.edit_deal(registration, project_title="PRINTERS  for city-hall")
        registration.refresh_from_db()
        self.assertFalse(registration.needs_review)

    def test_quantity_change_keeps_the_unit_price_and_goes_to_review(self):
        registration = self.registered_deal()
        line_id = registration.items.get().pk
        item = {
            "product_id": self.product.pk,
            "non_catalog_name": "",
            "quantity": 7,
            "requested_unit_price": "95.00",
            "justification": "",
        }
        self.assertEqual(self.edit_deal(registration, items=[item]).status_code, 200)
        registration.refresh_from_db()
        line = registration.items.get()
        self.assertEqual(line.pk, line_id)
        self.assertEqual(line.quantity, 7)
        self.assertEqual(str(line.list_unit_price_snapshot), "100.00")
        self.assertEqual(line.price_basis, RegistrationItem.PriceBasis.ORIGINAL)
        self.assertEqual(registration.status, Registration.Status.REVIEW_REQUIRED)
        self.assertTrue(registration.needs_review)

    def test_changed_product_is_repriced_on_that_line_only(self):
        registration = self.registered_deal()
        other = Product.objects.create(code="TEST-002", name="Other", category="Test category")
        ProductPrice.objects.create(product=other, unit_price="70.00", reason="Test price")
        kept = {
            "product_id": self.product.pk,
            "non_catalog_name": "",
            "quantity": 1,
            "requested_unit_price": "95.00",
            "justification": "",
        }
        added = {**kept, "product_id": other.pk, "requested_unit_price": "60.00"}
        self.assertEqual(self.edit_deal(registration, items=[kept, added]).status_code, 200)
        lines = {line.product_id: line for line in registration.items.all()}
        self.assertEqual(str(lines[self.product.pk].list_unit_price_snapshot), "100.00")
        self.assertEqual(lines[self.product.pk].price_basis, RegistrationItem.PriceBasis.ORIGINAL)
        self.assertEqual(str(lines[other.pk].list_unit_price_snapshot), "70.00")
        self.assertEqual(lines[other.pk].price_basis, RegistrationItem.PriceBasis.PRODUCT_CHANGED)

    def test_company_can_request_repricing_and_dbgi_reviews_it(self):
        registration = self.registered_deal()
        self.assertEqual(self.edit_deal(registration, request_repricing=True).status_code, 200)
        registration.refresh_from_db()
        item = registration.items.get()
        self.assertEqual(str(item.list_unit_price_snapshot), "150.00")
        self.assertEqual(item.price_basis, RegistrationItem.PriceBasis.COMPANY_REQUEST)
        self.assertEqual(registration.status, Registration.Status.REVIEW_REQUIRED)

    def test_end_user_change_goes_to_review_but_keeps_the_price(self):
        registration = self.registered_deal()
        other = EndUser.objects.create(
            official_name="Other End-user",
            city_municipality="Other City",
            street_address="Other address",
            status=EndUser.Status.VERIFIED,
            created_by=self.admin,
            verified_by=self.admin,
        )
        self.assertEqual(self.edit_deal(registration, end_user_id=other.pk).status_code, 200)
        registration.refresh_from_db()
        self.assertEqual(registration.status, Registration.Status.REVIEW_REQUIRED)
        self.assertEqual(str(registration.items.get().list_unit_price_snapshot), "100.00")

    def test_contact_fix_is_allowed_after_price_review_but_products_stay_locked(self):
        registration = self.registered_deal()
        registration.category_approvals.update(status=RegistrationCategoryApproval.Status.APPROVED)
        self.assertEqual(self.edit_deal(registration, contact_person="New Name").status_code, 200)
        item = {
            "product_id": self.product.pk,
            "non_catalog_name": "",
            "quantity": 9,
            "requested_unit_price": "95.00",
            "justification": "",
        }
        locked = self.edit_deal(registration, items=[item])
        self.assertEqual(locked.status_code, 409, locked.content)
        self.assertEqual(locked.json()["code"], "commercial_review_locked")

    def test_dbgi_repricing_needs_admin_and_a_reason_and_stops_at_price_review(self):
        registration = self.registered_deal()
        registration.refresh_from_db()
        url = f"/api/v1/review/registrations/{registration.pk}/reprice"
        body = json.dumps({"version": registration.version, "reason": "Scope was re-quoted."})
        self.client.force_login(self.user_a)
        denied = self.client.post(url, data=body, content_type="application/json")
        self.assertEqual(denied.status_code, 403)
        self.client.force_login(self.admin)
        response = self.client.post(url, data=body, content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        item = registration.items.get()
        self.assertEqual(str(item.list_unit_price_snapshot), "150.00")
        self.assertEqual(item.price_basis, RegistrationItem.PriceBasis.DBGI_DECISION)
        self.assertTrue(
            RegistrationNotification.objects.filter(
                recipient=self.user_a, title="List prices updated by DBGI"
            ).exists()
        )
        registration.refresh_from_db()
        registration.category_approvals.update(status=RegistrationCategoryApproval.Status.APPROVED)
        locked = self.client.post(
            url,
            data=json.dumps({"version": registration.version, "reason": "Scope was re-quoted."}),
            content_type="application/json",
        )
        self.assertEqual(locked.status_code, 409)

    def non_catalog_deal(self):
        self.set_price("100.00")
        registration = self.register_deal()
        line = registration.items.get()
        RegistrationItem.objects.filter(pk=line.pk).update(
            product=None,
            non_catalog_name="Special scanner",
            list_unit_price_snapshot="0.00",
            price_version=None,
        )
        registration.category_approvals.all().delete()
        registration.refresh_from_db()
        return registration, registration.items.get()

    def add_to_catalog(self, registration, line, **body):
        return self.client.post(
            f"/api/v1/review/registration-items/{line.pk}/catalog",
            data=json.dumps(
                {"version": registration.version, "reason": "Approved for the catalog.", **body}
            ),
            content_type="application/json",
        )

    NEW_PRODUCT: ClassVar[dict] = {
        "code": "SCAN-1",
        "name": "Scanner",
        "category": "Scanners",
        "list_price": "80.00",
    }

    def test_dbgi_adds_a_new_product_and_its_price_review_opens(self):
        registration, line = self.non_catalog_deal()
        self.client.force_login(self.user_a)
        denied = self.add_to_catalog(registration, line, new_product=self.NEW_PRODUCT)
        self.assertEqual(denied.status_code, 403)

        self.client.force_login(self.admin)
        response = self.add_to_catalog(registration, line, new_product=self.NEW_PRODUCT)

        self.assertEqual(response.status_code, 200, response.content)
        line.refresh_from_db()
        product = Product.objects.get(code="SCAN-1")
        self.assertEqual(line.product, product)
        self.assertEqual(line.non_catalog_name, "")
        self.assertEqual(str(line.list_unit_price_snapshot), "80.00")
        self.assertEqual(line.price_version.created_by, self.admin)
        self.assertEqual(
            registration.category_approvals.get(category="Scanners").status,
            RegistrationCategoryApproval.Status.PENDING,
        )
        self.assertIn(
            "Special scanner",
            registration.events.get(event_type="Product added to catalog").details,
        )
        self.assertTrue(
            RegistrationNotification.objects.filter(
                recipient=self.user_a, event_key=f"catalog-item:{line.pk}"
            ).exists()
        )
        again = self.add_to_catalog(
            Registration.objects.get(pk=registration.pk), line, new_product=self.NEW_PRODUCT
        )
        self.assertEqual(again.status_code, 400, again.content)

    def test_dbgi_can_link_an_existing_product_and_new_codes_must_be_unique(self):
        registration, line = self.non_catalog_deal()
        self.client.force_login(self.admin)
        neither = self.add_to_catalog(registration, line)
        self.assertEqual(neither.status_code, 400)
        duplicate = self.add_to_catalog(
            registration, line, new_product={**self.NEW_PRODUCT, "code": self.product.code}
        )
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(duplicate.json()["code"], "duplicate_product")

        linked = self.add_to_catalog(registration, line, product_id=self.product.pk)
        self.assertEqual(linked.status_code, 200, linked.content)
        line.refresh_from_db()
        self.assertEqual(line.product, self.product)
        self.assertEqual(str(line.list_unit_price_snapshot), "100.00")

    def test_a_decided_category_must_be_reopened_before_a_line_joins_it(self):
        registration, line = self.non_catalog_deal()
        RegistrationCategoryApproval.objects.create(
            registration=registration,
            category=self.product.category,
            status=RegistrationCategoryApproval.Status.APPROVED,
        )
        self.client.force_login(self.admin)
        response = self.add_to_catalog(registration, line, product_id=self.product.pk)
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(response.json()["code"], "commercial_review_locked")
        line.refresh_from_db()
        self.assertIsNone(line.product)

    def change_files_on_registered_deal(self):
        Registration.objects.filter(pk=self.registration_a.pk).update(
            status=Registration.Status.ELIGIBLE_MATCHED, needs_review=False
        )
        self.registration_a.refresh_from_db()
        version = self.registration_a.version
        self.client.force_login(self.user_a)
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            upload = self.client.post(
                f"/api/v1/registrations/{self.registration_a.pk}/attachments?version={version}",
                data={"file": SimpleUploadedFile("proof.pdf", b"%PDF-1.4 proof")},
            )
            self.assertEqual(upload.status_code, 201, upload.content)
            self.registration_a.refresh_from_db()
            flagged_before_finalize = self.registration_a.needs_review
            done = self.client.post(
                f"/api/v1/registrations/{self.registration_a.pk}/finalize",
                data=json.dumps({"version": version}),
                content_type="application/json",
            )
            self.assertEqual(done.status_code, 200, done.content)
        self.registration_a.refresh_from_db()
        return flagged_before_finalize

    def attachment_alerts(self):
        return RegistrationNotification.objects.filter(
            registration=self.registration_a,
            recipient=self.admin,
            title="Review needed: attachment files changed",
        )

    def test_file_change_on_a_registered_deal_alerts_dbgi_by_default(self):
        self.assertFalse(
            PortalSetting.objects.filter(alert_dbgi_on_attachment_change=False).exists()
        )
        self.assertTrue(self.change_files_on_registered_deal())
        self.assertTrue(self.registration_a.needs_review)
        self.assertEqual(self.registration_a.status, Registration.Status.ELIGIBLE_MATCHED)
        self.assertEqual(self.attachment_alerts().count(), 1)

    def test_file_change_alert_can_be_turned_off(self):
        PortalSetting.objects.update_or_create(
            key="portal", defaults={"alert_dbgi_on_attachment_change": False}
        )
        self.assertFalse(self.change_files_on_registered_deal())
        self.assertFalse(self.registration_a.needs_review)
        self.assertFalse(self.attachment_alerts().exists())
        self.assertTrue(self.registration_a.events.filter(event_type="Attachment added").exists())

    def test_removing_a_file_from_a_registered_deal_also_flags_it(self):
        self.change_files_on_registered_deal()
        Registration.objects.filter(pk=self.registration_a.pk).update(needs_review=False)
        self.registration_a.refresh_from_db()
        attachment = self.registration_a.attachments.get()
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.delete(
                f"/api/v1/attachments/{attachment.pk}?version={self.registration_a.version}"
            )
        self.assertEqual(response.status_code, 204, response.content)
        self.registration_a.refresh_from_db()
        self.assertTrue(self.registration_a.needs_review)

    def tied_project(self):
        opportunity = self.link_to_project(self.registration_a, self.registration_b)
        moment = timezone.now()
        Registration.objects.filter(pk__in=[self.registration_a.pk, self.registration_b.pk]).update(
            original_submitted_at=moment
        )
        return opportunity.scopes.get()

    def decide_tie(self, scope, order, reason="Better documents on file."):
        return self.client.post(
            f"/api/v1/review/opportunity-scopes/{scope.pk}/tie-decision",
            data=json.dumps({"order": order, "reason": reason}),
            content_type="application/json",
        )

    def ranks(self):
        rows = self.client.get("/api/v1/rankings").json()["items"][0]["entries"]
        return {row["registration_id"]: row for row in rows}

    def test_tie_is_shared_until_dbgi_decides_the_order(self):
        scope = self.tied_project()
        a, b = self.registration_a.pk, self.registration_b.pk
        self.client.force_login(self.admin)
        before = self.ranks()
        self.assertTrue(before[a]["is_tied"] and before[b]["is_tied"])
        self.assertEqual((before[a]["rank"], before[b]["rank"]), (1, 1))

        self.client.force_login(self.user_a)
        self.assertEqual(self.decide_tie(scope, [b, a]).status_code, 403)

        self.client.force_login(self.admin)
        self.assertEqual(self.decide_tie(scope, [b, a]).status_code, 200)
        after = self.ranks()
        self.assertEqual((after[b]["rank"], after[a]["rank"]), (1, 2))
        self.assertFalse(after[a]["is_tied"])
        self.assertEqual(after[a]["tie_reason"], "Better documents on file.")
        url = reverse("admin:registrations_opportunityranking_changelist")
        self.assertEqual(self.client.get(url).status_code, 200)

        self.client.force_login(self.user_a)
        own = self.ranks()
        self.assertEqual(list(own), [a])
        self.assertEqual(own[a]["rank"], 2)
        self.assertIsNone(own[a]["tie_reason"])
        notice = RegistrationNotification.objects.get(
            recipient=self.user_a, title="Tied ranking decided"
        )
        self.assertNotIn("Better documents", notice.message)
        event = self.registration_a.events.get(event_type="Tied ranking decided")
        self.assertNotIn("Better documents", event.details)

    def test_tie_decision_must_list_the_whole_tie_once(self):
        scope = self.tied_project()
        a, b = self.registration_a.pk, self.registration_b.pk
        self.client.force_login(self.admin)
        self.assertEqual(self.decide_tie(scope, [a, a]).status_code, 400)
        self.assertEqual(self.decide_tie(scope, [a, 999999]).status_code, 400)
        Registration.objects.filter(pk=b).update(
            original_submitted_at=timezone.now() + timedelta(seconds=1)
        )
        self.assertEqual(self.decide_tie(scope, [a, b]).status_code, 400)
        self.assertFalse(RankingTieDecision.objects.exists())

    def test_latest_tie_decision_applies_and_a_decision_cannot_be_edited(self):
        scope = self.tied_project()
        a, b = self.registration_a.pk, self.registration_b.pk
        self.client.force_login(self.admin)
        self.decide_tie(scope, [a, b])
        self.decide_tie(scope, [b, a], reason="Corrected after checking.")
        self.assertEqual(RankingTieDecision.objects.count(), 2)
        self.assertEqual(self.ranks()[b]["rank"], 1)
        decision = RankingTieDecision.objects.first()
        decision.reason = "Changed"
        with self.assertRaises(ValidationError):
            decision.save()

    def test_decided_tie_keeps_later_places_and_survives_a_withdrawal(self):
        scope = self.tied_project()
        third_company = Company.objects.create(name="Third Dealer")
        third_user = User.objects.create_user(
            username="dealer-c", password="example-password", company=third_company
        )
        third = self.make_registration(third_company, third_user, "Third project")
        Registration.objects.filter(pk=third.pk).update(
            status=Registration.Status.ELIGIBLE_MATCHED,
            opportunity_scope=scope,
            original_submitted_at=timezone.now() + timedelta(days=1),
        )
        a, b = self.registration_a.pk, self.registration_b.pk
        self.client.force_login(self.admin)
        self.decide_tie(scope, [b, a])
        self.assertEqual(self.ranks()[third.pk]["rank"], 3)

        Registration.objects.filter(pk=b).update(status=Registration.Status.WITHDRAWN)
        remaining = self.ranks()
        self.assertEqual(remaining[a]["rank"], 1)
        self.assertFalse(remaining[a]["is_tied"])
        self.assertEqual(remaining[third.pk]["rank"], 2)

    def approve_in_admin(self, approval, valid_until=""):
        return self.client.post(
            reverse("admin:registrations_registrationcategoryapproval_change", args=[approval.pk]),
            {
                "registration": approval.registration_id,
                "category": approval.category,
                "status": RegistrationCategoryApproval.Status.APPROVED,
                "rationale": "Within the allowed discount.",
                "valid_until": valid_until,
                "item_approvals-TOTAL_FORMS": "0",
                "item_approvals-INITIAL_FORMS": "0",
                "item_approvals-MIN_NUM_FORMS": "0",
                "item_approvals-MAX_NUM_FORMS": "1000",
            },
        )

    def test_price_approved_in_django_admin_defaults_to_90_days(self):
        self.set_price("100.00")
        approval = self.register_deal().category_approvals.get()
        self.client.force_login(self.admin)
        response = self.approve_in_admin(approval)
        self.assertEqual(response.status_code, 302, response.content[:1500])
        approval.refresh_from_db()
        self.assertEqual(approval.valid_until, timezone.localdate() + timedelta(days=90))

        response = self.approve_in_admin(approval, "2027-06-30")
        self.assertEqual(response.status_code, 302, response.content[:1500])
        approval.refresh_from_db()
        self.assertEqual(approval.valid_until, date(2027, 6, 30))

    def test_price_of_a_withdrawn_deal_cannot_be_decided_in_django_admin(self):
        self.set_price("100.00")
        registration = self.register_deal()
        approval = registration.category_approvals.get()
        Registration.objects.filter(pk=registration.pk).update(status=Registration.Status.WITHDRAWN)
        self.client.force_login(self.admin)
        response = self.approve_in_admin(approval)
        self.assertEqual(response.status_code, 403)
        approval.refresh_from_db()
        self.assertEqual(approval.status, RegistrationCategoryApproval.Status.PENDING)

    def test_project_put_on_hold_in_django_admin_starts_the_60_day_clock(self):
        opportunity = self.link_to_project(self.registration_a)
        self.client.force_login(self.admin)
        url = reverse("admin:registrations_opportunity_change", args=[opportunity.pk])
        scope = opportunity.scopes.get()
        body = {
            "title": opportunity.title,
            "end_user": opportunity.end_user_id,
            "end_user_name": opportunity.end_user_name,
            "end_user_address": opportunity.end_user_address,
            "project_status": Opportunity.ProjectStatus.ON_HOLD,
            "is_active": "on",
            "scopes-TOTAL_FORMS": "1",
            "scopes-INITIAL_FORMS": "1",
            "scopes-MIN_NUM_FORMS": "0",
            "scopes-MAX_NUM_FORMS": "1000",
            "scopes-0-id": scope.pk,
            "scopes-0-opportunity": opportunity.pk,
            "scopes-0-name": scope.name,
            "scopes-0-scope_type": scope.scope_type,
            "scopes-0-is_active": "on",
        }
        response = self.client.post(url, body)
        self.assertEqual(response.status_code, 302, response.content[:1500])
        opportunity.refresh_from_db()
        self.assertIsNotNone(opportunity.on_hold_since)
        summary = process_deadlines(now=opportunity.on_hold_since + timedelta(days=60))
        self.assertEqual(summary.hold_limits_reached, 1)

        response = self.client.post(url, {**body, "project_status": "active"})
        self.assertEqual(response.status_code, 302, response.content[:1500])
        opportunity.refresh_from_db()
        self.assertIsNone(opportunity.on_hold_since)

    def test_renewal_can_be_requested_and_decided_from_the_registration(self):
        self.set_price("100.00")
        registration = self.register_deal()
        approval = registration.category_approvals.get()
        RegistrationCategoryApproval.objects.filter(pk=approval.pk).update(
            status=RegistrationCategoryApproval.Status.APPROVED,
            valid_until=timezone.localdate() + timedelta(days=10),
        )
        detail = self.client.get(f"/api/v1/registrations/{registration.pk}").json()
        self.assertTrue(detail["category_approvals"][0]["can_request_renewal"])

        requested = self.client.post(
            f"/api/v1/category-approvals/{approval.pk}/renewals",
            data=json.dumps({"reason": "The bid was moved to next month."}),
            content_type="application/json",
        )
        self.assertEqual(requested.status_code, 201, requested.content)
        self.assertFalse(requested.json()["can_request_renewal"])
        renewal_id = requested.json()["pending_renewal_id"]

        self.client.force_login(self.admin)
        decided = self.client.post(
            f"/api/v1/review/renewals/{renewal_id}/decision",
            data=json.dumps({"approve": True, "reason": "The new bid date is confirmed."}),
            content_type="application/json",
        )
        self.assertEqual(decided.status_code, 200, decided.content)
        self.assertIsNone(decided.json()["pending_renewal_id"])
        approval.refresh_from_db()
        self.assertEqual(approval.valid_until, timezone.localdate() + timedelta(days=40))
        self.assertTrue(
            RegistrationNotification.objects.filter(
                recipient=self.user_a, title="Price renewal approved"
            ).exists()
        )

        Registration.objects.filter(pk=registration.pk).update(status=Registration.Status.WITHDRAWN)
        self.client.force_login(self.user_a)
        refused = self.client.post(
            f"/api/v1/category-approvals/{approval.pk}/renewals",
            data=json.dumps({"reason": "The bid was moved again."}),
            content_type="application/json",
        )
        self.assertEqual(refused.status_code, 409, refused.content)

    def approve_price(self, registration, unit_price="9000.00", valid_days=30):
        approval = registration.category_approvals.get()
        RegistrationCategoryApproval.objects.filter(pk=approval.pk).update(
            status=RegistrationCategoryApproval.Status.APPROVED,
            valid_until=timezone.localdate() + timedelta(days=valid_days),
        )
        for item in registration.items.all():
            RegistrationItemApproval.objects.create(
                category_approval=approval, registration_item=item, approved_unit_price=unit_price
            )
        return approval

    def priced_deal(self, company_user=None):
        self.set_price("10000.00")
        registration = self.register_deal()
        if company_user:
            Registration.objects.filter(pk=registration.pk).update(
                company=company_user.company, submitted_by=company_user
            )
            registration.refresh_from_db()
        return registration

    def request_repeat(self, registration, *, confirmed=True, quantity=5, noa=None):
        item = registration.items.first()
        return self.client.post(
            f"/api/v1/registrations/{registration.pk}/repeat-orders",
            data={
                "noa": noa or SimpleUploadedFile("noa.pdf", b"%PDF-1.4 notice of award"),
                "ntp": SimpleUploadedFile("ntp.pdf", b"%PDF-1.4 notice to proceed"),
                "lines": json.dumps([{"item_id": item.pk, "quantity": quantity}]),
                "letters_confirmed": "true" if confirmed else "false",
                "note": "Five more printers for the same office.",
            },
        )

    def decide_repeat(self, repeat_order_id, accept=True):
        return self.client.post(
            f"/api/v1/review/repeat-orders/{repeat_order_id}/decision",
            data=json.dumps({"accept": accept, "reason": "The letters say it is a repeat order."}),
            content_type="application/json",
        )

    def test_repeat_order_needs_a_valid_approved_price_and_both_letters(self):
        registration = self.priced_deal()
        self.link_to_project(registration)
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.client.force_login(self.user_a)
            self.assertEqual(self.request_repeat(registration).status_code, 400)

            approval = self.approve_price(registration)
            detail = self.client.get(f"/api/v1/registrations/{registration.pk}").json()
            self.assertEqual(len(detail["repeat_order_choices"]), 1)
            self.assertEqual(self.request_repeat(registration, confirmed=False).status_code, 400)
            wrong_file = SimpleUploadedFile("noa.exe", b"not a letter")
            self.assertEqual(self.request_repeat(registration, noa=wrong_file).status_code, 400)
            self.assertEqual(RepeatOrder.objects.count(), 0)

            RegistrationCategoryApproval.objects.filter(pk=approval.pk).update(
                valid_until=timezone.localdate() - timedelta(days=1)
            )
            self.assertEqual(self.request_repeat(registration).status_code, 400)

    def test_repeat_order_is_decided_by_dbgi_and_keeps_its_price(self):
        registration = self.priced_deal()
        self.link_to_project(registration)
        self.approve_price(registration)
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.client.force_login(self.user_a)
            created = self.request_repeat(registration)
            self.assertEqual(created.status_code, 201, created.content)
            body = created.json()
            self.assertEqual(body["status_label"], "Waiting for DBGI")
            self.assertEqual(Decimal(body["total"]), Decimal("45000.00"))
            self.assertFalse(body["can_decide"])
            self.assertTrue(
                RegistrationNotification.objects.filter(
                    recipient=self.admin, title="Repeat order requested"
                ).exists()
            )
            self.assertEqual(self.client.get(body["noa_url"]).status_code, 200)

            self.client.force_login(self.user_b)
            self.assertEqual(self.client.get(body["noa_url"]).status_code, 404)
            refused = self.decide_repeat(body["id"])
            self.assertEqual(refused.status_code, 403)

            self.client.force_login(self.admin)
            self.assertEqual(self.client.get(body["ntp_url"]).status_code, 200)
            decided = self.decide_repeat(body["id"])
            self.assertEqual(decided.status_code, 200, decided.content)
            self.assertEqual(decided.json()["status"], "accepted")
            self.assertEqual(self.decide_repeat(body["id"]).status_code, 404)
            self.assertTrue(
                RegistrationNotification.objects.filter(
                    recipient=self.user_a, title="Repeat order accepted"
                ).exists()
            )
            RegistrationItemApproval.objects.filter(
                registration_item__registration=registration
            ).update(approved_unit_price="8000.00")
            self.client.force_login(self.user_a)
            detail = self.client.get(f"/api/v1/registrations/{registration.pk}").json()
            self.assertEqual(Decimal(detail["repeat_orders"][0]["total"]), Decimal("45000.00"))

    def test_repeat_order_cannot_be_accepted_after_the_price_ended_or_on_a_withdrawn_deal(self):
        registration = self.priced_deal()
        self.link_to_project(registration)
        approval = self.approve_price(registration)
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.client.force_login(self.user_a)
            repeat_id = self.request_repeat(registration).json()["id"]
            RegistrationCategoryApproval.objects.filter(pk=approval.pk).update(
                valid_until=timezone.localdate() - timedelta(days=1)
            )
            self.client.force_login(self.admin)
            ended = self.decide_repeat(repeat_id)
            self.assertEqual(ended.status_code, 400)
            self.assertEqual(ended.json()["code"], "price_not_active")
            Registration.objects.filter(pk=registration.pk).update(
                status=Registration.Status.WITHDRAWN
            )
            self.assertEqual(self.decide_repeat(repeat_id, accept=False).status_code, 409)

    def two_projects(self):
        first = self.priced_deal()
        self.link_to_project(first)
        second = self.register_deal()
        Registration.objects.filter(pk=second.pk).update(
            company=self.company_b, submitted_by=self.user_b
        )
        self.link_to_project(second)
        first.refresh_from_db()
        second.refresh_from_db()
        return first, second

    def merge(self, source, target, **overrides):
        body = {
            "target_scope_id": target.opportunity_scope_id,
            "reason": "DBGI learned these are the same tender.",
            "price_action": "keep",
            **overrides,
        }
        return self.client.post(
            f"/api/v1/review/opportunity-scopes/{source.opportunity_scope_id}/merge",
            data=json.dumps(body),
            content_type="application/json",
        )

    def test_merge_keeps_submission_times_and_only_dbgi_reads_the_reason(self):
        first, second = self.two_projects()
        original_time = second.original_submitted_at
        self.approve_price(first)
        self.client.force_login(self.user_a)
        self.assertEqual(self.merge(second, first).status_code, 403)

        self.client.force_login(self.admin)
        preview = self.client.get(
            f"/api/v1/review/opportunity-scopes/{second.opportunity_scope_id}/merge-preview"
            f"?target_scope_id={first.opportunity_scope_id}"
        ).json()
        self.assertEqual([row["registration_id"] for row in preview["rows"]], [first.pk, second.pk])
        self.assertEqual(preview["deals_moving"], 1)
        source_scope = second.opportunity_scope
        response = self.merge(second, first)
        self.assertEqual(response.status_code, 200, response.content)

        second.refresh_from_db()
        source_scope.refresh_from_db()
        self.assertEqual(second.opportunity_scope_id, first.opportunity_scope_id)
        self.assertEqual(second.original_submitted_at, original_time)
        self.assertFalse(source_scope.is_active)
        self.assertFalse(source_scope.opportunity.is_active)
        first.refresh_from_db()
        self.assertEqual(first.category_approvals.get().status, "approved")

        self.client.force_login(self.user_b)
        detail = self.client.get(f"/api/v1/registrations/{second.pk}").json()
        event = next(item for item in detail["events"] if item["event_type"] == "Project merged")
        self.assertNotIn("same tender", event["details"])
        self.assertIn("combined", event["details"])
        rankings = self.client.get("/api/v1/rankings").json()["items"]
        self.assertEqual(rankings[0]["entries"][0]["rank"], 2)
        self.client.force_login(self.admin)
        detail = self.client.get(f"/api/v1/registrations/{second.pk}").json()
        event = next(item for item in detail["events"] if item["event_type"] == "Project merged")
        self.assertIn("same tender", event["details"])

    def test_merge_can_set_the_order_and_send_prices_back_for_review(self):
        first, second = self.two_projects()
        self.approve_price(second)
        self.client.force_login(self.admin)
        invalid = self.merge(second, first, order=[first.pk])
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(self.merge(second, second).status_code, 400)

        response = self.merge(second, first, order=[second.pk, first.pk], price_action="review")
        self.assertEqual(response.status_code, 200, response.content)
        approval = second.category_approvals.get()
        self.assertEqual(approval.status, RegistrationCategoryApproval.Status.PENDING)
        self.assertFalse(approval.item_approvals.exists())
        self.assertIsNone(approval.valid_until)
        entries = self.client.get("/api/v1/rankings").json()["items"][0]["entries"]
        ranks = {entry["registration_id"]: entry["rank"] for entry in entries}
        self.assertEqual(ranks, {second.pk: 1, first.pk: 2})

    def deal_with_two_products(self):
        other = Product.objects.create(code="SPLIT-1", name="Split product", category="Scanners")
        ProductPrice.objects.create(product=other, unit_price="500.00", reason="Test price")
        registration = self.priced_deal()
        RegistrationItem.objects.create(
            registration=registration, product=other, quantity=2, requested_unit_price="400.00"
        )
        RegistrationCategoryApproval.objects.create(registration=registration, category="Scanners")
        self.link_to_project(registration)
        registration.refresh_from_db()
        return registration, registration.items.get(product=other)

    def split(self, registration, item, **overrides):
        body = {
            "item_ids": [item.pk],
            "new_lot_name": "Lot 2",
            "reason": "The tender has two separate lots.",
            "price_action": "keep",
            **overrides,
        }
        return self.client.post(
            f"/api/v1/review/registrations/{registration.pk}/split",
            data=json.dumps(body),
            content_type="application/json",
        )

    def test_split_moves_products_to_a_new_deal_with_the_original_time(self):
        registration, item = self.deal_with_two_products()
        self.client.force_login(self.user_a)
        self.assertEqual(self.split(registration, item).status_code, 403)

        self.client.force_login(self.admin)
        detail = self.client.get(f"/api/v1/registrations/{registration.pk}").json()
        self.assertTrue(detail["can_split"])
        all_items = list(registration.items.values_list("pk", flat=True))
        self.assertEqual(self.split(registration, item, item_ids=all_items).status_code, 400)
        response = self.split(registration, item)
        self.assertEqual(response.status_code, 201, response.content)

        created = Registration.objects.get(pk=response.json()["id"])
        self.assertEqual(created.original_submitted_at, registration.original_submitted_at)
        self.assertEqual(created.status, Registration.Status.ELIGIBLE_MATCHED)
        self.assertEqual(created.company_id, registration.company_id)
        self.assertEqual(created.opportunity_scope.name, "Lot 2")
        self.assertEqual(created.opportunity_scope.scope_type, OpportunityScope.ScopeType.LOT)
        self.assertEqual(list(created.items.values_list("pk", flat=True)), [item.pk])
        self.assertEqual(created.category_approvals.get().category, "Scanners")
        self.assertEqual(registration.category_approvals.count(), 1)
        self.assertEqual(created.competitor_items.count(), registration.competitor_items.count())
        self.assertEqual(self.split(registration, item).status_code, 400)
        self.client.force_login(self.user_a)
        new_detail = self.client.get(f"/api/v1/registrations/{created.pk}").json()
        event = new_detail["events"][0]
        self.assertNotIn("two separate lots", event["details"])

    def test_split_shares_a_price_decision_between_both_deals_and_copies_files(self):
        registration = self.priced_deal()
        second_item = RegistrationItem.objects.create(
            registration=registration,
            product=self.product,
            quantity=3,
            requested_unit_price="8500.00",
        )
        self.link_to_project(registration)
        self.approve_price(registration)
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            attachment = RegistrationAttachment(
                registration=registration,
                original_name="support.pdf",
                uploaded_by=self.user_a,
            )
            attachment.file.save("support.pdf", SimpleUploadedFile("s.pdf", b"%PDF-1.4 x"))
            self.client.force_login(self.admin)
            response = self.split(registration, second_item, new_lot_name="Lot B")
            self.assertEqual(response.status_code, 201, response.content)
            created = Registration.objects.get(pk=response.json()["id"])
            copy = created.attachments.get()
            self.assertNotEqual(copy.file.name, attachment.file.name)
            attachment.delete()
            self.assertTrue(copy.file.storage.exists(copy.file.name))
        kept = registration.category_approvals.get()
        moved = created.category_approvals.get()
        self.assertEqual(moved.status, "approved")
        self.assertEqual(moved.valid_until, kept.valid_until)
        self.assertEqual(moved.item_approvals.get().registration_item_id, second_item.pk)
        self.assertEqual(kept.item_approvals.count(), 1)

    def test_split_waits_for_pending_repeat_orders(self):
        registration, item = self.deal_with_two_products()
        approval = registration.category_approvals.get(category=self.product.category)
        RegistrationCategoryApproval.objects.filter(pk=approval.pk).update(
            status=RegistrationCategoryApproval.Status.APPROVED,
            valid_until=timezone.localdate() + timedelta(days=30),
        )
        first_item = registration.items.get(product=self.product)
        RegistrationItemApproval.objects.create(
            category_approval=approval,
            registration_item=first_item,
            approved_unit_price="9000.00",
        )
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.client.force_login(self.user_a)
            self.assertEqual(self.request_repeat(registration).status_code, 201)
            self.client.force_login(self.admin)
            response = self.split(registration, item)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "repeat_order_pending")

    def test_working_days_skip_weekends_holidays_and_time_after_the_cutoff(self):
        manila = ZoneInfo("Asia/Manila")
        wednesday = datetime(2026, 11, 4, 10, 0, tzinfo=manila)
        self.assertEqual(add_working_days(wednesday, 1), date(2026, 11, 5))
        after_cutoff = datetime(2026, 11, 4, 17, 0, tzinfo=manila)
        self.assertEqual(add_working_days(after_cutoff, 1), date(2026, 11, 6))
        friday = datetime(2026, 11, 6, 10, 0, tzinfo=manila)
        self.assertEqual(add_working_days(friday, 1), date(2026, 11, 9))
        saturday = datetime(2026, 11, 7, 10, 0, tzinfo=manila)
        self.assertEqual(add_working_days(saturday, 1), date(2026, 11, 10))
        PublicHoliday.objects.create(date=date(2026, 11, 5), name="Test holiday")
        self.assertEqual(add_working_days(wednesday, 1), date(2026, 11, 6))

    def test_nationwide_holidays_are_already_counted(self):
        manila = ZoneInfo("Asia/Manila")
        before_christmas = datetime(2026, 12, 23, 10, 0, tzinfo=manila)
        self.assertEqual(add_working_days(before_christmas, 1), date(2026, 12, 28))
        self.assertTrue(PublicHoliday.objects.filter(date=date(2027, 3, 26)).exists())

    def ranked_deals(self):
        """Three companies on one project, ranked 1, 2, and 3."""
        self.set_price("10000.00")
        company_c = Company.objects.create(name="East Dealer")
        user_c = User.objects.create_user(
            "dealer-c", password="example-password", company=company_c
        )
        deals = [self.register_deal(), self.register_deal(), self.register_deal()]
        for deal, user in zip(deals[1:], (self.user_b, user_c)):
            Registration.objects.filter(pk=deal.pk).update(company=user.company, submitted_by=user)
        self.link_to_project(*deals)
        for deal in deals:
            deal.refresh_from_db()
        return deals

    def approve_with_warnings(self, deal, price):
        approval = deal.category_approvals.get()
        item = deal.items.get()
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin:registrations_registrationcategoryapproval_change", args=[approval.pk]),
            {
                "registration": deal.pk,
                "category": approval.category,
                "status": RegistrationCategoryApproval.Status.APPROVED,
                "rationale": "Within the allowed discount.",
                "valid_until": "",
                "item_approvals-TOTAL_FORMS": "1",
                "item_approvals-INITIAL_FORMS": "0",
                "item_approvals-MIN_NUM_FORMS": "0",
                "item_approvals-MAX_NUM_FORMS": "1000",
                "item_approvals-0-registration_item": item.pk,
                "item_approvals-0-approved_unit_price": price,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(RegistrationItemApproval.objects.filter(registration_item=item).exists())
        return [str(message) for message in response.context["messages"]]

    def test_price_form_shows_the_rank_and_the_project_prices(self):
        first, second, _ = self.ranked_deals()
        self.approve_price(first, unit_price="8000.00")
        self.client.force_login(self.admin)
        url = reverse(
            "admin:registrations_registrationcategoryapproval_change",
            args=[second.category_approvals.get().pk],
        )
        response = self.client.get(url)
        self.assertContains(response, "Rank on this project")
        self.assertContains(response, "Rank 1: North Dealer")
        self.assertContains(response, "8,000.00")

    def test_following_the_price_rule_gives_no_warning(self):
        first, second, third = self.ranked_deals()
        self.assertFalse(self.rule_warnings(self.approve_with_warnings(first, "8000.00")))
        self.assertFalse(self.rule_warnings(self.approve_with_warnings(second, "9000.00")))
        self.assertFalse(self.rule_warnings(self.approve_with_warnings(third, "9000.00")))

    def test_breaking_the_price_rule_warns_but_still_saves(self):
        first, second, third = self.ranked_deals()
        self.approve_with_warnings(first, "8000.00")
        same_as_first = self.rule_warnings(self.approve_with_warnings(second, "8000.00"))
        self.assertTrue(any("Rank 1 should have the best price" in text for text in same_as_first))
        different = self.rule_warnings(self.approve_with_warnings(third, "9000.00"))
        self.assertTrue(any("should have the same price" in text for text in different))

    def test_rank_1_is_warned_when_decided_last_with_a_worse_price(self):
        first, second, _ = self.ranked_deals()
        self.approve_with_warnings(second, "9000.00")
        warnings = self.rule_warnings(self.approve_with_warnings(first, "9500.00"))
        self.assertTrue(any("Rank 1 should have the best price" in text for text in warnings))

    def test_tied_first_place_asks_dbgi_to_decide_the_tie(self):
        first, second, _ = self.ranked_deals()
        Registration.objects.filter(pk=second.pk).update(
            original_submitted_at=first.original_submitted_at
        )
        self.approve_with_warnings(first, "8000.00")
        warnings = self.rule_warnings(self.approve_with_warnings(second, "8000.00"))
        self.assertTrue(any("Decide the tie first" in text for text in warnings))

    def rule_warnings(self, messages):
        return [text for text in messages if "should have" in text or "Decide the tie" in text]

    def test_clearing_removes_newer_records_and_their_letters(self):
        first, second = self.two_projects()
        self.approve_price(first)
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.client.force_login(self.user_a)
            self.assertEqual(self.request_repeat(first).status_code, 201)
            letter = RepeatOrder.objects.get().noa_file
            self.assertTrue(letter.storage.exists(letter.name))
            ProjectOutcomeReport.objects.create(
                registration=first,
                opportunity=first.opportunity_scope.opportunity,
                outcome=ProjectOutcomeReport.Outcome.WON,
                note="Test report",
                reported_by=self.user_a,
            )
            RankingTieDecision.objects.create(
                opportunity_scope=first.opportunity_scope,
                submitted_at=first.original_submitted_at,
                order=[first.pk],
                reason="Test reason",
                decided_by=self.admin,
            )
            self.client.force_login(self.admin)
            self.assertEqual(self.merge(second, first).status_code, 200)
            with self.captureOnCommitCallbacks(execute=True):
                counts = clear_transactional_records()
            self.assertEqual(counts["repeat_orders"], 1)
            self.assertEqual(counts["project_changes"], 1)
            self.assertFalse(letter.storage.exists(letter.name))
        self.assertEqual(sum(transactional_record_counts().values()), 0)
        self.assertTrue(User.objects.filter(pk=self.user_a.pk).exists())
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())
