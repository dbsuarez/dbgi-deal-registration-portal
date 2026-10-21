import json
from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

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

from .admin import RegistrationAdmin
from .audit import registration_change_summary
from .matching import generate_matching_suggestion
from .models import (
    Company,
    CompetitorBrand,
    CompetitorBrandAlias,
    CompetitorItem,
    EndUser,
    NotificationEventSetting,
    Opportunity,
    OpportunityScope,
    PriceApprovalRenewal,
    Product,
    Registration,
    RegistrationAttachment,
    RegistrationCategoryApproval,
    RegistrationEvent,
    RegistrationItem,
    RegistrationItemApproval,
    RegistrationNotification,
    RegistrationReviewDecision,
    User,
)


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
        self.client.force_login(self.admin)

        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/registrations/admin.css")
        self.assertContains(response, "Site administration")

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

    def test_session_and_product_options(self):
        self.client.force_login(self.user_a)
        session = self.client.get("/api/v1/session")
        products = self.client.get("/api/v1/products")
        self.assertEqual(session.status_code, 200)
        self.assertTrue(session.json()["csrf_token"])
        self.assertEqual(products.status_code, 200)
        self.assertIn(self.product.code, {item["code"] for item in products.json()})

    def test_competitor_brand_options_return_active_master_data(self):
        CompetitorBrand.objects.create(name="Active brand")
        CompetitorBrand.objects.create(name="Archived brand", is_active=False)
        self.client.force_login(self.user_a)
        response = self.client.get("/api/v1/competitor-brands")

        self.assertEqual(response.status_code, 200)
        self.assertTrue({"Canon", "Epson", "HP", "Lexmark"}.issubset(response.json()))
        self.assertIn("Active brand", response.json())
        self.assertNotIn("Archived brand", response.json())

    def test_registration_adds_new_competitor_brand_to_master_data(self):
        self.client.force_login(self.user_a)
        payload = self.payload()
        payload["competitor_items"][0]["brand"] = "  New Brand  "

        response = self.client.post(
            "/api/v1/registrations",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201, response.content)
        brand = CompetitorBrand.objects.get(normalized_name="new brand")
        self.assertEqual(brand.name, "New Brand")

    def test_competitor_brand_alias_resolves_to_canonical_brand(self):
        self.client.force_login(self.user_a)
        payload = self.payload()
        payload["competitor_items"][0]["brand"] = "  hewlett PACKARD  "

        response = self.client.post(
            "/api/v1/registrations",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201, response.content)
        registration = Registration.objects.get(pk=response.json()["id"])
        self.assertEqual(registration.competitor_items.get().brand, "HP")
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
            RegistrationNotification.objects.filter(registration=registration).values_list(
                "recipient__username", flat=True
            )
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
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.user_a.email])
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
        self.product.list_price = "125.00"
        self.product.save(update_fields=["list_price"])
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
        self.product.list_price = "125.00"
        self.product.save(update_fields=["list_price"])
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
            data=json.dumps({"version": version, "evidence_changed": True}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["version"], version + 1)
        self.registration_a.refresh_from_db()
        self.assertTrue(self.registration_a.needs_review)
        self.assertTrue(self.registration_a.events.filter(event_type="Evidence submitted").exists())

        stale = self.client.post(
            f"/api/v1/registrations/{self.registration_a.pk}/finalize",
            data=json.dumps({"version": version}),
            content_type="application/json",
        )
        self.assertEqual(stale.status_code, 409, stale.content)
        self.assertEqual(stale.json()["code"], "edit_conflict")
