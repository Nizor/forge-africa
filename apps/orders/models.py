import uuid
from django.db import models
from apps.quotes.models import Quote


class Order(models.Model):
    PENDING_PAYMENT = 'PENDING_PAYMENT'
    DEPOSIT_PAID = 'DEPOSIT_PAID'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (PENDING_PAYMENT, 'Pending Payment'),
        (DEPOSIT_PAID, 'Deposit Paid'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote = models.OneToOneField(Quote, on_delete=models.CASCADE, related_name='order')
    deposit_percentage = models.PositiveIntegerField(default=30)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING_PAYMENT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Order for {self.quote.rfq.short_id}'

    @property
    def rfq(self):
        return self.quote.rfq

    @property
    def client(self):
        return self.quote.rfq.client


class Payment(models.Model):
    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (SUCCESS, 'Success'),
        (FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    gateway = models.CharField(max_length=50, default='paystack')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    gateway_response = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Payment {self.reference} — ₦{self.amount:,.2f} ({self.status})'
