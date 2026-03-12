import uuid
from django.db import models
from apps.rfqs.models import RFQ
from apps.bids.models import Bid


class Quote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rfq = models.OneToOneField(RFQ, on_delete=models.CASCADE, related_name='quote')
    selected_bid = models.ForeignKey(Bid, on_delete=models.PROTECT, related_name='quote')
    final_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Final price shown to client (may include Forge Africa margin)'
    )
    forge_margin_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='Forge Africa margin % added on top of vendor bid'
    )
    deposit_percentage = models.PositiveIntegerField(
        default=30,
        help_text='Deposit % required from client to start the project'
    )
    admin_notes = models.TextField(blank=True, help_text='Message to client about this quote')
    sent_to_client_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Quote for {self.rfq.short_id} — ₦{self.final_price:,.2f}'
