import uuid
from django.db import models
from django.conf import settings
from apps.rfqs.models import RFQ


class Bid(models.Model):
    SUBMITTED = 'SUBMITTED'
    UNDER_REVIEW = 'UNDER_REVIEW'
    SELECTED = 'SELECTED'
    NOT_SELECTED = 'NOT_SELECTED'
    REVISION_REQUESTED = 'REVISION_REQUESTED'

    STATUS_CHOICES = [
        (SUBMITTED, 'Submitted'),
        (UNDER_REVIEW, 'Under Review'),
        (SELECTED, 'Selected'),
        (NOT_SELECTED, 'Not Selected'),
        (REVISION_REQUESTED, 'Revision Requested'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name='bids')
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bids'
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)
    timeline_days = models.PositiveIntegerField(help_text='Estimated delivery in working days')
    notes = models.TextField(blank=True, help_text='Technical notes, approach, terms')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SUBMITTED)
    admin_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price']
        unique_together = ['rfq', 'vendor']
        verbose_name = 'Bid'

    def __str__(self):
        return f'Bid by {self.vendor.get_full_name()} on {self.rfq.short_id} — ₦{self.price:,.2f}'

    @property
    def short_id(self):
        return str(self.id)[:8].upper()


class BidAttachment(models.Model):
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='bid_attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
