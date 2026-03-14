"""
Unit tests for all models — properties, relationships, calculations.
Run: python manage.py test tests.test_models
"""
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from apps.accounts.models import User
from apps.rfqs.models import RFQ, ServiceCategory
from apps.bids.models import Bid
from apps.quotes.models import Quote
from apps.orders.models import Order
from .factories import (
    make_client, make_vendor, make_admin,
    make_category, make_rfq, make_bid, make_quote, make_order
)


class UserModelTest(TestCase):

    def test_client_role_properties(self):
        user = make_client()
        self.assertTrue(user.is_client)
        self.assertFalse(user.is_vendor)
        self.assertFalse(user.is_forge_admin)

    def test_vendor_role_properties(self):
        user = make_vendor()
        self.assertFalse(user.is_client)
        self.assertTrue(user.is_vendor)
        self.assertFalse(user.is_forge_admin)

    def test_admin_role_properties(self):
        user = make_admin()
        self.assertFalse(user.is_client)
        self.assertFalse(user.is_vendor)
        self.assertTrue(user.is_forge_admin)

    def test_get_full_name(self):
        user = make_client()
        self.assertEqual(user.get_full_name(), 'Test Client')

    def test_email_is_unique(self):
        make_client(email='unique@test.com')
        with self.assertRaises(Exception):
            make_client(email='unique@test.com')

    def test_verification_token_is_uuid(self):
        user = make_client()
        import uuid
        self.assertIsInstance(user.verification_token, uuid.UUID)

    def test_unverified_user_default(self):
        user = make_client(verified=False)
        self.assertFalse(user.is_verified)

    def test_str_representation(self):
        user = make_client()
        self.assertIn('CLIENT', str(user))
        self.assertIn('Test Client', str(user))


class ServiceCategoryModelTest(TestCase):

    def test_category_creation(self):
        cat = make_category()
        self.assertEqual(cat.name, 'Metal Fabrication')
        self.assertTrue(cat.is_active)

    def test_slug_is_unique(self):
        make_category(slug='unique-slug')
        with self.assertRaises(Exception):
            ServiceCategory.objects.create(
                name='Another', slug='unique-slug', is_active=True
            )

    def test_str_representation(self):
        cat = make_category()
        self.assertEqual(str(cat), 'Metal Fabrication')


class RFQModelTest(TestCase):

    def test_rfq_creation(self):
        rfq = make_rfq()
        self.assertIsNotNone(rfq.pk)
        self.assertEqual(rfq.status, RFQ.SUBMITTED)

    def test_short_id_is_8_chars(self):
        rfq = make_rfq()
        self.assertEqual(len(rfq.short_id), 8)
        self.assertEqual(rfq.short_id, rfq.short_id.upper())

    def test_can_accept_bids_when_open(self):
        rfq = make_rfq(status=RFQ.BIDDING_OPEN)
        self.assertTrue(rfq.can_accept_bids)

    def test_cannot_accept_bids_when_not_open(self):
        for status in [RFQ.DRAFT, RFQ.SUBMITTED, RFQ.APPROVED, RFQ.BIDDING_CLOSED]:
            rfq = make_rfq(status=status)
            self.assertFalse(rfq.can_accept_bids)

    def test_has_quote_false_initially(self):
        rfq = make_rfq()
        self.assertFalse(rfq.has_quote)

    def test_has_quote_true_after_quote_created(self):
        bid = make_bid()
        quote = make_quote(rfq=bid.rfq, bid=bid)
        bid.rfq.refresh_from_db()
        self.assertTrue(bid.rfq.has_quote)

    def test_status_color_mapping(self):
        rfq = make_rfq(status=RFQ.BIDDING_OPEN)
        self.assertEqual(rfq.status_color, 'yellow')

    def test_rfq_ordered_by_newest_first(self):
        client = make_client()
        rfq1 = make_rfq(client=client)
        rfq2 = make_rfq(client=client)
        rfqs = list(RFQ.objects.filter(client=client))
        self.assertEqual(rfqs[0].pk, rfq2.pk)


class BidModelTest(TestCase):

    def test_bid_creation(self):
        bid = make_bid()
        self.assertIsNotNone(bid.pk)
        self.assertEqual(bid.status, Bid.SUBMITTED)

    def test_bid_price_stored_as_decimal(self):
        bid = make_bid(price=Decimal('175000.50'))
        bid.refresh_from_db()
        self.assertEqual(bid.price, Decimal('175000.50'))

    def test_unique_bid_per_vendor_per_rfq(self):
        rfq = make_rfq(status=RFQ.BIDDING_OPEN)
        vendor = make_vendor()
        Bid.objects.create(
            rfq=rfq, vendor=vendor, price=Decimal('100000'),
            timeline_days=14, status=Bid.SUBMITTED
        )
        with self.assertRaises(Exception):
            Bid.objects.create(
                rfq=rfq, vendor=vendor, price=Decimal('90000'),
                timeline_days=10, status=Bid.SUBMITTED
            )

    def test_bids_ordered_by_price_ascending(self):
        rfq = make_rfq(status=RFQ.BIDDING_OPEN)
        make_bid(rfq=rfq, price=Decimal('200000'))
        make_bid(rfq=rfq, price=Decimal('100000'))
        bids = list(rfq.bids.all())
        self.assertLess(bids[0].price, bids[1].price)

    def test_str_representation(self):
        bid = make_bid()
        self.assertIn('₦', str(bid))


class QuoteModelTest(TestCase):

    def test_quote_creation(self):
        quote = make_quote()
        self.assertIsNotNone(quote.pk)

    def test_margin_stored_correctly(self):
        bid = make_bid(price=Decimal('100000'))
        quote = make_quote(bid=bid, margin_pct=Decimal('15.00'))
        self.assertEqual(quote.forge_margin_percentage, Decimal('15.00'))

    def test_deposit_percentage_stored(self):
        quote = make_quote(deposit_pct=25)
        self.assertEqual(quote.deposit_percentage, 25)

    def test_quote_str(self):
        quote = make_quote()
        self.assertIn('₦', str(quote))
        self.assertIn('Quote for', str(quote))


class OrderModelTest(TestCase):

    def test_order_creation(self):
        order = make_order()
        self.assertEqual(order.status, Order.PENDING_PAYMENT)

    def test_deposit_calculation(self):
        bid = make_bid(price=Decimal('100000'))
        quote = make_quote(bid=bid, final_price=Decimal('115000'), deposit_pct=30)
        order = make_order(quote=quote)
        self.assertEqual(order.deposit_amount, Decimal('34500.00'))
        self.assertEqual(order.balance_due, Decimal('80500.00'))
        self.assertEqual(order.total_amount, Decimal('115000'))

    def test_rfq_property(self):
        order = make_order()
        self.assertEqual(order.rfq, order.quote.rfq)

    def test_client_property(self):
        order = make_order()
        self.assertEqual(order.client, order.quote.rfq.client)

    def test_deposit_matches_percentage(self):
        quote = make_quote(final_price=Decimal('200000'), deposit_pct=25)
        order = make_order(quote=quote)
        expected = Decimal('200000') * Decimal('0.25')
        self.assertAlmostEqual(float(order.deposit_amount), float(expected), places=2)
