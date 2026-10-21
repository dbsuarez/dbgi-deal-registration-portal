import re
from decimal import Decimal
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


ATTACHMENT_SIGNATURES = {
    "pdf": (b"%PDF-",),
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "docx": (b"PK\x03\x04",),
    "xlsx": (b"PK\x03\x04",),
}


def validate_attachment_content(upload):
    """Reject files whose first bytes do not match the declared extension."""
    extension = Path(getattr(upload, "name", "") or "").suffix.lower().lstrip(".")
    signatures = ATTACHMENT_SIGNATURES.get(extension)
    if not signatures:
        raise ValidationError("Attachments must be a PDF, PNG, JPEG, DOCX, or XLSX file.")
    upload.seek(0)
    header = upload.read(8)
    upload.seek(0)
    if not any(header.startswith(signature) for signature in signatures):
        raise ValidationError(
            "The file content does not match its extension. Upload the original document."
        )


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
    currency = models.CharField(max_length=3, default="PHP")
    list_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
    )
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
    class ProjectStatus(models.TextChoices):
        UPCOMING = "upcoming", "Upcoming"
        ACTIVE = "active", "Active"
        WON = "won", "Won"
        LOST = "lost", "Lost"
        CANCELLED = "cancelled", "Cancelled"
        ON_HOLD = "on_hold", "On hold"

    end_user = models.ForeignKey(
        EndUser, on_delete=models.PROTECT, null=True, blank=True, related_name="opportunities"
    )
    title = models.CharField(max_length=240)
    end_user_name = models.CharField(max_length=240)
    end_user_address = models.TextField()
    project_status = models.CharField(
        max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.UPCOMING
    )
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
        ELIGIBLE_MATCHED = "eligible_matched", "Registered"
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
        indexes = [
            models.Index(fields=["company", "-created_at"], name="reg_company_created_idx"),
            models.Index(
                fields=["status", "opportunity_scope", "original_submitted_at", "id"],
                name="reg_rank_lookup_idx",
            ),
        ]

    # Evidence is frozen once a reviewer has it or a decision exists, so an
    # upload or delete can never change what a decision was based on.
    EVIDENCE_LOCKED_STATUSES = frozenset({Status.UNDER_REVIEW, Status.APPROVED, Status.REJECTED})

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

    @property
    def project_status(self):
        if not self.opportunity_scope_id:
            return None
        return self.opportunity_scope.opportunity.project_status

    @property
    def project_status_label(self):
        if not self.opportunity_scope_id:
            return "Not linked"
        return self.opportunity_scope.opportunity.get_project_status_display()

    @property
    def price_status(self):
        approvals = list(self.category_approvals.all())
        if not approvals:
            return "not_requested"
        statuses = {approval.effective_status for approval in approvals}
        if statuses == {RegistrationCategoryApproval.Status.APPROVED}:
            return "approved"
        if statuses == {RegistrationCategoryApproval.Status.EXPIRED}:
            return "expired"
        if RegistrationCategoryApproval.Status.CHANGES_REQUESTED in statuses:
            return "changes_requested"
        if statuses == {RegistrationCategoryApproval.Status.REJECTED}:
            return "rejected"
        if statuses == {RegistrationCategoryApproval.Status.PENDING}:
            return "pending"
        return "partially_approved"

    @property
    def price_status_label(self):
        labels = {
            "not_requested": "Not requested",
            "pending": "Pending",
            "changes_requested": "Changes requested",
            "partially_approved": "Partially approved",
            "approved": "Approved",
            "rejected": "Rejected",
            "expired": "Expired",
        }
        return labels[self.price_status]


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


class CompetitorBrand(models.Model):
    name = models.CharField(max_length=160)
    normalized_name = models.CharField(max_length=160, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]

    def clean(self):
        super().clean()
        self.name = " ".join(self.name.split())
        if not self.name:
            raise ValidationError({"name": "Enter a competitor brand name."})
        self.normalized_name = self.name.casefold()
        if CompetitorBrandAlias.objects.filter(normalized_name=self.normalized_name).exists():
            raise ValidationError(
                {"name": "This name is already assigned as a competitor brand alias."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CompetitorBrandAlias(models.Model):
    brand = models.ForeignKey(CompetitorBrand, on_delete=models.CASCADE, related_name="aliases")
    name = models.CharField(max_length=160)
    normalized_name = models.CharField(max_length=160, unique=True, editable=False)

    class Meta:
        ordering = ["name", "id"]
        verbose_name_plural = "competitor brand aliases"

    def clean(self):
        super().clean()
        self.name = " ".join(self.name.split())
        if not self.name:
            raise ValidationError({"name": "Enter a competitor brand alias."})
        self.normalized_name = self.name.casefold()
        if CompetitorBrand.objects.filter(normalized_name=self.normalized_name).exists():
            raise ValidationError({"name": "This name is already assigned to a competitor brand."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} -> {self.brand.name}"


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
    currency = models.CharField(max_length=3, default="PHP")
    list_unit_price_snapshot = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
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

    @property
    def requested_discount_percent(self):
        if self.list_unit_price_snapshot <= 0:
            return None
        return (
            (self.list_unit_price_snapshot - self.requested_unit_price)
            / self.list_unit_price_snapshot
            * Decimal("100")
        ).quantize(Decimal("0.01"))

    @property
    def requested_total(self):
        return (self.requested_unit_price * self.quantity).quantize(Decimal("0.01"))

    def __str__(self):
        return self.display_name


class RegistrationCategoryApproval(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CHANGES_REQUESTED = "changes_requested", "Changes requested"
        PARTIALLY_APPROVED = "partially_approved", "Partially approved"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"

    registration = models.ForeignKey(
        Registration, on_delete=models.PROTECT, related_name="category_approvals"
    )
    category = models.CharField(max_length=120)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    rationale = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True, related_name="category_approvals"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["registration", "category"], name="unique_category_approval"
            )
        ]

    @property
    def effective_status(self):
        if (
            self.status in {self.Status.APPROVED, self.Status.PARTIALLY_APPROVED}
            and self.valid_until
            and self.valid_until < timezone.localdate()
        ):
            return self.Status.EXPIRED
        return self.status

    def __str__(self):
        return f"{self.registration.reference} - {self.category}"


class RegistrationItemApproval(models.Model):
    category_approval = models.ForeignKey(
        RegistrationCategoryApproval, on_delete=models.CASCADE, related_name="item_approvals"
    )
    registration_item = models.OneToOneField(
        RegistrationItem, on_delete=models.PROTECT, related_name="price_approval"
    )
    approved_unit_price = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    remarks = models.TextField(blank=True)

    def clean(self):
        super().clean()
        if self.registration_item.registration_id != self.category_approval.registration_id:
            raise ValidationError("The approved item must belong to the same registration.")


class PriceApprovalRenewal(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    category_approval = models.ForeignKey(
        RegistrationCategoryApproval, on_delete=models.PROTECT, related_name="renewals"
    )
    requested_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="price_renewal_requests"
    )
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    previous_valid_until = models.DateField(null=True, blank=True)
    new_valid_until = models.DateField(null=True, blank=True)
    decided_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="price_renewal_decisions",
    )
    decision_reason = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-requested_at", "-id"]


class RegistrationEvent(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="registration_events"
    )
    event_type = models.CharField(max_length=80)
    details = models.TextField(blank=True)
    snapshot = models.JSONField(default=dict, blank=True)
    resulting_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.registration.reference}: {self.event_type}"


class RegistrationNotification(models.Model):
    class EventType(models.TextChoices):
        SUBMISSION_CONFIRMED = "submission_confirmed", "Submission confirmed"
        REGISTRATION_DECISION = "registration_decision", "Registration decision"
        PRICE_DECISION = "price_decision", "Price decision"

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="registration_notifications"
    )
    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="notifications"
    )
    event_type = models.CharField(max_length=40, choices=EventType.choices)
    event_key = models.CharField(max_length=120)
    title = models.CharField(max_length=200)
    message = models.TextField()
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "event_key"], name="unique_recipient_notification_event"
            )
        ]
        indexes = [
            models.Index(
                fields=["recipient", "read_at", "-created_at"],
                name="reg_notice_inbox_idx",
            )
        ]

    def __str__(self):
        return f"{self.recipient}: {self.title}"


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
            validate_attachment_content,
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
