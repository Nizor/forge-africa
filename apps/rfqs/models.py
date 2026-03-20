import uuid
from django.db import models
from django.conf import settings


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='🔧', help_text='Emoji or icon class')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Service Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class RFQ(models.Model):
    # Status choices
    DRAFT = 'DRAFT'
    SUBMITTED = 'SUBMITTED'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    BIDDING_OPEN = 'BIDDING_OPEN'
    BIDDING_CLOSED = 'BIDDING_CLOSED'
    QUOTE_SENT = 'QUOTE_SENT'
    ACCEPTED = 'ACCEPTED'
    DEPOSIT_PAID = 'DEPOSIT_PAID'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (SUBMITTED, 'Submitted'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (BIDDING_OPEN, 'Bidding Open'),
        (BIDDING_CLOSED, 'Bidding Closed'),
        (QUOTE_SENT, 'Quote Sent'),
        (ACCEPTED, 'Accepted'),
        (DEPOSIT_PAID, 'Deposit Paid'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]

    STATUS_COLORS = {
        DRAFT: 'gray',
        SUBMITTED: 'blue',
        APPROVED: 'indigo',
        REJECTED: 'red',
        BIDDING_OPEN: 'yellow',
        BIDDING_CLOSED: 'orange',
        QUOTE_SENT: 'purple',
        ACCEPTED: 'teal',
        DEPOSIT_PAID: 'green',
        IN_PROGRESS: 'cyan',
        COMPLETED: 'emerald',
        CANCELLED: 'red',
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rfqs'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.PROTECT, related_name='rfqs'
    )
    quantity = models.PositiveIntegerField(default=1)
    materials = models.CharField(max_length=255, blank=True, help_text='e.g. Stainless Steel, PLA, Aluminium')
    deadline = models.DateField(help_text='Desired completion date')
    budget_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    additional_notes = models.TextField(blank=True)

    phone = models.CharField(
    max_length=20, blank=True,
    help_text='Contact number for admin to reach client if needed'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)

    # Admin fields
    admin_notes = models.TextField(blank=True, help_text='Internal Forge Africa notes')
    rejection_reason = models.TextField(blank=True)
    bidding_deadline = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'RFQ'
        verbose_name_plural = 'RFQs'

    def __str__(self):
        return f'RFQ-{str(self.id)[:8].upper()} | {self.title}'

    @property
    def short_id(self):
        return str(self.id)[:8].upper()

    @property
    def status_color(self):
        return self.STATUS_COLORS.get(self.status, 'gray')

    @property
    def can_accept_bids(self):
        return self.status == self.BIDDING_OPEN

    @property
    def has_quote(self):
        return hasattr(self, 'quote')


class RFQAttachment(models.Model):
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='rfq_attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.filename} ({self.rfq.short_id})'
