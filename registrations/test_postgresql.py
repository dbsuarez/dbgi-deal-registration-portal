import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier
from unittest import skipUnless

from django.db import IntegrityError, close_old_connections, connection, connections, transaction
from django.test import Client, TransactionTestCase

from .models import (
    Company,
    EndUser,
    MatchingSuggestion,
    Product,
    Registration,
    RegistrationItem,
    User,
)


@skipUnless(connection.vendor == "postgresql", "PostgreSQL integration test")
class PostgreSQLConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Concurrency Dealer")
        self.user = User.objects.create_user(
            username="concurrency-dealer",
            password="example-password",
            company=self.company,
        )
        self.admin = User.objects.create_superuser(
            username="concurrency-admin",
            email="admin@example.invalid",
            password="example-password",
        )
        self.end_user = EndUser.objects.create(
            official_name="Concurrency End-user",
            city_municipality="Test City",
            street_address="Test Street",
            status=EndUser.Status.VERIFIED,
            created_by=self.admin,
            verified_by=self.admin,
        )
        self.product = Product.objects.create(
            code="CONCURRENCY-001",
            name="Concurrency product",
            category="Test category",
        )
        self.registration = Registration.objects.create(
            company=self.company,
            submitted_by=self.user,
            end_user=self.end_user,
            end_user_name=self.end_user.official_name,
            end_user_address=self.end_user.full_address,
            project_title="Concurrency registration",
            bid_date=date(2026, 11, 30),
            delivery_date=date(2027, 1, 30),
            contact_person="Test person",
            contact_designation="Buyer",
            contact_email="test@example.invalid",
            contact_number="0000000000",
            evidence_description="Test evidence",
            evidence_sharing_confirmed=True,
        )
        RegistrationItem.objects.create(
            registration=self.registration,
            product=self.product,
            quantity=1,
            requested_unit_price="100.00",
        )

    def _concurrent_requests(self, method, url, payload, user_id):
        barrier = Barrier(2)

        def send():
            close_old_connections()
            client = Client()
            client.force_login(User.objects.get(pk=user_id))
            barrier.wait()
            response = getattr(client, method)(
                url,
                data=json.dumps(payload),
                content_type="application/json",
            )
            connections.close_all()
            return response.status_code, response.json()

        with ThreadPoolExecutor(max_workers=2) as executor:
            return list(executor.map(lambda _: send(), range(2)))

    def test_concurrent_finalize_serializes_and_rejects_stale_version(self):
        responses = self._concurrent_requests(
            "post",
            f"/api/v1/registrations/{self.registration.pk}/finalize",
            {"version": self.registration.version, "evidence_changed": True},
            self.user.pk,
        )

        self.registration.refresh_from_db()
        self.assertEqual(sorted(status for status, _ in responses), [200, 409])
        conflict = next(body for status, body in responses if status == 409)
        self.assertEqual(conflict["code"], "edit_conflict")
        self.assertEqual(self.registration.version, 2)
        self.assertEqual(
            self.registration.events.filter(event_type="Evidence submitted").count(), 1
        )

    def test_concurrent_registration_edits_reject_one_stale_version(self):
        payload = {
            "version": self.registration.version,
            "end_user_id": self.end_user.pk,
            "project_title": "Concurrently edited registration",
            "bid_date": "2026-11-30",
            "delivery_date": "2027-01-30",
            "contact_person": "Test person",
            "contact_designation": "Buyer",
            "contact_email": "test@example.invalid",
            "contact_number": "0000000000",
            "evidence_description": "Test evidence",
            "evidence_url": "",
            "evidence_sharing_confirmed": True,
            "competitor_items": [
                {
                    "brand": "Concurrency competitor",
                    "item_name": "Competitor product",
                    "bid_price": "120.00",
                    "remarks": "Concurrency test",
                }
            ],
            "items": [
                {
                    "product_id": self.product.pk,
                    "non_catalog_name": "",
                    "quantity": 1,
                    "requested_unit_price": "100.00",
                    "justification": "Concurrency test",
                }
            ],
        }

        responses = self._concurrent_requests(
            "put",
            f"/api/v1/registrations/{self.registration.pk}",
            payload,
            self.user.pk,
        )

        self.registration.refresh_from_db()
        self.assertEqual(sorted(status for status, _ in responses), [200, 409])
        conflict = next(body for status, body in responses if status == 409)
        self.assertEqual(conflict["code"], "edit_conflict")
        self.assertEqual(self.registration.version, 2)
        self.assertEqual(self.registration.events.filter(event_type="Company edit").count(), 1)

    def test_concurrent_matching_refresh_keeps_one_current_suggestion(self):
        responses = self._concurrent_requests(
            "post",
            f"/api/v1/review/registrations/{self.registration.pk}/suggestion",
            {},
            self.admin.pk,
        )

        self.assertEqual([status for status, _ in responses], [200, 200])
        self.assertEqual(
            MatchingSuggestion.objects.filter(
                registration=self.registration,
                is_current=True,
            ).count(),
            1,
        )

    def test_concurrent_normalized_end_users_enforce_database_uniqueness(self):
        barrier = Barrier(2)

        def create_candidate(index):
            close_old_connections()
            barrier.wait()
            try:
                with transaction.atomic():
                    EndUser.objects.create(
                        official_name="Duplicate Agency",
                        city_municipality="Test City",
                        street_address="Same Address",
                        created_by_id=self.admin.pk,
                    )
                result = "created"
            except IntegrityError:
                result = "duplicate"
            connections.close_all()
            return result

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(create_candidate, range(2)))

        self.assertEqual(sorted(results), ["created", "duplicate"])
        self.assertEqual(
            EndUser.objects.filter(
                normalized_name="duplicate agency",
                normalized_address="same address test city",
                is_active=True,
            ).count(),
            1,
        )
