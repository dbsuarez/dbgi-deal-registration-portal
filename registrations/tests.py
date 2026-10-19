import json
from datetime import date
from io import StringIO
from tempfile import TemporaryDirectory

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import (
    Company,
    CompetitorItem,
    Opportunity,
    Product,
    Registration,
    RegistrationAttachment,
    RegistrationEvent,
    RegistrationItem,
    RegistrationReviewDecision,
    User,
)


class RegistrationApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company_a = Company.objects.create(name="North Dealer")
        cls.company_b = Company.objects.create(name="South Dealer")
        cls.user_a = User.objects.create_user(
            username="dealer-a", password="example-password", company=cls.company_a
        )
        cls.user_b = User.objects.create_user(
            username="dealer-b", password="example-password", company=cls.company_b
        )
        cls.admin = User.objects.create_superuser(
            username="dbgi-admin",
            email="admin@example.invalid",
            password="example-password",
        )
        cls.product = Product.objects.create(
            code="TEST-001", name="Test item", category="Test category"
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
            "end_user_name": "TEST end user",
            "end_user_address": "TEST address",
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

    def test_list_and_detail_are_company_scoped(self):
        self.client.force_login(self.user_a)
        response = self.client.get("/api/v1/registrations?page=1&page_size=10")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 1)
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

    def test_company_user_can_reach_admin_login_to_switch_accounts(self):
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
        self.assertContains(response, "Site administration")

    def test_session_and_product_options(self):
        self.client.force_login(self.user_a)
        session = self.client.get("/api/v1/session")
        products = self.client.get("/api/v1/products")
        self.assertEqual(session.status_code, 200)
        self.assertTrue(session.json()["csrf_token"])
        self.assertEqual(products.status_code, 200)
        self.assertIn(self.product.code, {item["code"] for item in products.json()})

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
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            upload = self.client.post(
                f"/api/v1/registrations/{self.registration_a.pk}/attachments?description=Support",
                data={"file": SimpleUploadedFile("support.pdf", b"valid evidence")},
            )
            self.assertEqual(upload.status_code, 201, upload.content)
            attachment_id = upload.json()["id"]

            download = self.client.get(reverse("registration-attachment", args=[attachment_id]))
            self.assertEqual(download.status_code, 200)
            self.assertEqual(download["Cache-Control"], "private, no-store")
            self.assertEqual(b"".join(download.streaming_content), b"valid evidence")

            self.client.force_login(self.user_b)
            hidden = self.client.get(reverse("registration-attachment", args=[attachment_id]))
            self.assertEqual(hidden.status_code, 404)

            self.client.force_login(self.user_a)
            with self.captureOnCommitCallbacks(execute=True):
                deleted = self.client.delete(f"/api/v1/attachments/{attachment_id}")
            self.assertEqual(deleted.status_code, 204)
            self.assertFalse(RegistrationAttachment.objects.filter(pk=attachment_id).exists())

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

    def test_cannot_upload_attachment_to_other_company(self):
        self.client.force_login(self.user_a)
        response = self.client.post(
            f"/api/v1/registrations/{self.registration_b.pk}/attachments",
            data={"file": SimpleUploadedFile("support.pdf", b"valid evidence")},
        )
        self.assertEqual(response.status_code, 404)
