import re
from pathlib import Path
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone


def registration_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"private/registrations/{uuid4().hex}{extension}"


def validate_attachment_size(upload):
    max_bytes = 10 * 1024 * 1024
    if upload.size > max_bytes:
        raise ValidationError("Attachments must be no larger than 10 MB.")


class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)
    partner_code = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        COMPANY = "company", "Company user"
        DBGI_ADMIN = "dbgi_admin", "DBGI admin"

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.COMPANY)

    @property
    def is_dbgi_admin(self):
        return self.is_superuser or (self.is_staff and self.role == self.Role.DBGI_ADMIN)

    def clean(self):
        super().clean()
        if self.role == self.Role.COMPANY and not self.company_id and not self.is_superuser:
            raise ValidationError({"company": "Company users must belong to a company."})
        if self.role == self.Role.DBGI_ADMIN and self.company_id:
            raise ValidationError({"company": "DBGI admins must not be assigned to a company."})
        if self.role == self.Role.DBGI_ADMIN and not self.is_staff:
            raise ValidationError({"is_staff": "DBGI admins must have staff access."})


class Product(models.Model):
    code = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=240)
    category = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code", "name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


def normalize_end_user_value(value):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", value.lower()).split())


class EndUser(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending verification"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    official_name = models.CharField(max_length=240)
    acronym = models.CharField(max_length=80, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="sub_organizations"
    )
    government_branch = models.CharField(max_length=120, blank=True)
    organization_type = models.CharField(max_length=160, blank=True)
    sector = models.CharField(max_length=160, blank=True)
    region = models.CharField(max_length=160, blank=True)
    province = models.CharField(max_length=160, blank=True)
    city_municipality = models.CharField(max_length=160)
    street_address = models.TextField()
    postal_code = models.CharField(max_length=20, blank=True)
    philgeps_reference = models.CharField(max_length=120, blank=True)
    source_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    is_active = models.BooleanField(default=True)
    proposed_by_company = models.ForeignKey(
        Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="proposed_end_users"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_end_users"
    )
    verified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_end_users"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    normalized_name = models.CharField(max_length=240, editable=False)
    normalized_address = models.TextField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["official_name", "id"]
        indexes = [
            models.Index(fields=["status", "is_active"]),
            models.Index(fields=["normalized_name"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["normalized_name", "normalized_address"],
                condition=models.Q(is_active=True),
                name="unique_active_normalized_end_user",
            )
        ]
        verbose_name = "End-user"
        verbose_name_plural = "End-users"

    @property
    def full_address(self):
        return ", ".join(
            part
            for part in (
                self.street_address,
                self.city_municipality,
                self.province,
                self.region,
                self.postal_code,
            )
            if part
        )

    def save(self, *args, **kwargs):
        self.normalized_name = normalize_end_user_value(self.official_name)
        self.normalized_address = normalize_end_user_value(self.full_address)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.official_name


class EndUserAlias(models.Model):
    end_user = models.ForeignKey(EndUser, on_delete=models.CASCADE, related_name="aliases")
    name = models.CharField(max_length=240)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["end_user", "name"], name="unique_end_user_alias")
        ]
        verbose_name = "End-user alias"
        verbose_name_plural = "End-user aliases"

    def __str__(self):
        return self.name


class Opportunity(models.Model):
    end_user = models.ForeignKey(
        EndUser, on_delete=models.PROTECT, null=True, blank=True, related_name="opportunities"
    )
    title = models.CharField(max_length=240)
    end_user_name = models.CharField(max_length=240)
    end_user_address = models.TextField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="opportunities")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title", "id"]
        indexes = [models.Index(fields=["is_active", "end_user_name"])]
        verbose_name_plural = "opportunities"

    def __str__(self):
        return self.title


class OpportunityScope(models.Model):
    class ScopeType(models.TextChoices):
        WHOLE = "whole", "Whole opportunity"
        LOT = "lot", "Specific lot"

    opportunity = models.ForeignKey(Opportunity, on_delete=models.PROTECT, related_name="scopes")
    name = models.CharField(max_length=200)
    scope_type = models.CharField(max_length=10, choices=ScopeType.choices)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["opportunity__title", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["opportunity", "name"], name="unique_scope_name_per_opportunity"
            )
        ]

    def __str__(self):
        return f"{self.opportunity.title} | {self.name}"


class Registration(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        CHANGES_REQUESTED = "changes_requested", "Changes requested"
        RESUBMITTED = "resubmitted", "Resubmitted"
        ELIGIBLE_MATCHED = "eligible_matched", "Eligible and matched"
        REVIEW_REQUIRED = "review_required", "Review required after edit"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="registrations")
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="registrations")
    end_user = models.ForeignKey(
        EndUser, on_delete=models.PROTECT, null=True, blank=True, related_name="registrations"
    )
    end_user_name = models.CharField(max_length=240)
    end_user_address = models.TextField()
    project_title = models.CharField(max_length=240)
    bid_date = models.DateField()
    delivery_date = models.DateField()
    contact_person = models.CharField(max_length=200)
    contact_designation = models.CharField(max_length=160)
    contact_email = models.EmailField()
    contact_number = models.CharField(max_length=40)
    evidence_description = models.TextField(default="")
    evidence_url = models.URLField(blank=True)
    evidence_sharing_confirmed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    needs_review = models.BooleanField(default=False)
    opportunity_scope = models.ForeignKey(
        OpportunityScope,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="registrations",
    )
    original_submitted_at = models.DateTimeField(default=timezone.now, editable=False)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def reference(self):
        return f"DBGI-{self.pk:06d}" if self.pk else "New registration"

    def clean(self):
        super().clean()
        if not self.evidence_description.strip():
            raise ValidationError(
                {"evidence_description": "Describe the evidence for this opportunity."}
            )
        if not self.evidence_sharing_confirmed:
            raise ValidationError(
                {
                    "evidence_sharing_confirmed": (
                        "Confirm that you are authorized to share this evidence."
                    )
                }
            )

    def __str__(self):
        return f"{self.reference} - {self.project_title}"


class OpportunityRanking(Registration):
    class Meta:
        proxy = True
        verbose_name = "opportunity ranking"
        verbose_name_plural = "opportunity rankings"


class MatchingSuggestion(models.Model):
    class Outcome(models.TextChoices):
        SAME_SCOPE = "same_scope", "Same opportunity and scope"
        NEW_SCOPE = "new_scope", "Same opportunity with a new scope"
        DIFFERENT = "different", "Different opportunity"
        CLARIFY = "clarify", "Request clarification"

    class Confidence(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="matching_suggestions"
    )
    candidate_scope = models.ForeignKey(
        OpportunityScope,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="matching_suggestions",
    )
    outcome = models.CharField(max_length=20, choices=Outcome.choices)
    confidence = models.CharField(max_length=10, choices=Confidence.choices)
    score = models.PositiveSmallIntegerField()
    supporting_factors = models.JSONField(default=list)
    conflicting_factors = models.JSONField(default=list)
    rule_version = models.CharField(max_length=40, default="matching-v1")
    is_current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["registration"],
                condition=models.Q(is_current=True),
                name="one_current_matching_suggestion",
            )
        ]


class RegistrationReviewDecision(models.Model):
    class Decision(models.TextChoices):
        START_REVIEW = "start_review", "Start review"
        REQUEST_CHANGES = "request_changes", "Request changes"
        CONFIRM_MATCH = "confirm_match", "Confirm eligible match"
        REJECT = "reject", "Reject"

    registration = models.ForeignKey(
        Registration, on_delete=models.PROTECT, related_name="review_decisions"
    )
    suggestion = models.ForeignKey(
        MatchingSuggestion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="decisions",
    )
    opportunity_scope = models.ForeignKey(
        OpportunityScope,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="review_decisions",
    )
    decision = models.CharField(max_length=30, choices=Decision.choices)
    rationale = models.TextField()
    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="review_decisions")
    registration_version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class CompetitorItem(models.Model):
    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="competitor_items"
    )
    brand = models.CharField(max_length=160)
    item_name = models.CharField(max_length=200)
    bid_price = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(0)]
    )
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.brand} - {self.item_name}"


class RegistrationItem(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, null=True, blank=True, related_name="registration_items"
    )
    non_catalog_name = models.CharField(max_length=240, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    requested_unit_price = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(0)]
    )
    justification = models.TextField(blank=True)

    def clean(self):
        super().clean()
        if not self.product_id and not self.non_catalog_name.strip():
            raise ValidationError(
                {"non_catalog_name": "Choose a catalog product or enter a product description."}
            )

    @property
    def display_name(self):
        return str(self.product) if self.product_id else self.non_catalog_name

    def __str__(self):
        return self.display_name


class RegistrationEvent(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="registration_events"
    )
    event_type = models.CharField(max_length=80)
    details = models.TextField(blank=True)
    snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.registration.reference}: {self.event_type}"


class RegistrationAttachment(models.Model):
    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(
        upload_to=registration_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=("pdf", "png", "jpg", "jpeg", "docx", "xlsx")
            ),
            validate_attachment_size,
        ],
    )
    original_name = models.CharField(max_length=255)
    description = models.CharField(max_length=240, blank=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="registration_attachments"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return self.original_name


@receiver(post_delete, sender=RegistrationAttachment)
def delete_registration_attachment_file(sender, instance, **kwargs):
    if instance.file:
        storage = instance.file.storage
        file_name = instance.file.name
        transaction.on_commit(lambda: storage.delete(file_name))
