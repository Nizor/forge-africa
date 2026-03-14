"""
Tests for the full RFQ workflow — submit, approve, reject, bid, select, quote, accept.
Run: python manage.py test tests.test_rfq_workflow
"""
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, Client as TestClient
from apps.rfqs.models import RFQ
from apps.bids.models import Bid
from apps.quotes.models import Quote
from apps.orders.models import Order
from .factories import (
    make_client, make_vendor, make_admin,
    make_category, make_rfq, make_bid, make_quote, make_order
)


class RFQSubmissionTest(TestCase):

    def setUp(self):
        self.tc = TestClient()
        self.client_user = make_client(email='client@test.com', verified=True)
        self.category = make_category()
        self.tc.login(email='client@test.com', password='testpass123')

    def test_rfq_create_page_loads(self):
        response = self.tc.get('/client/rfq/new/')
        self.assertEqual(response.status_code, 200)

    def test_client_can_submit_rfq(self):
        response = self.tc.post('/client/rfq/new/', {
            'title': 'Steel Brackets Order',
            'description': 'Need 200 steel L-brackets for furniture.',
            'category': self.category.pk,
            'quantity': 200,
            'materials': 'Stainless Steel',
            'deadline': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
        })
        self.assertTrue(RFQ.objects.filter(
            client=self.client_user, title='Steel Brackets Order'
        ).exists())

    def test_submitted_rfq_has_submitted_status(self):
        self.tc.post('/client/rfq/new/', {
            'title': 'Plastic Parts',
            'description': 'Need injection moulded plastic parts.',
            'category': self.category.pk,
            'quantity': 1000,
            'deadline': (date.today() + timedelta(days=20)).strftime('%Y-%m-%d'),
        })
        rfq = RFQ.objects.filter(client=self.client_user).first()
        self.assertEqual(rfq.status, RFQ.SUBMITTED)

    def test_client_can_view_own_rfq(self):
        rfq = make_rfq(client=self.client_user)
        response = self.tc.get(f'/client/rfq/{rfq.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_client_cannot_view_other_client_rfq(self):
        other_client = make_client(email='other@test.com')
        rfq = make_rfq(client=other_client)
        response = self.tc.get(f'/client/rfq/{rfq.pk}/')
        self.assertNotEqual(response.status_code, 200)

    def test_past_deadline_rejected(self):
        response = self.tc.post('/client/rfq/new/', {
            'title': 'Past Deadline RFQ',
            'description': 'Test',
            'category': self.category.pk,
            'quantity': 10,
            'deadline': (date.today() - timedelta(days=1)).strftime('%Y-%m-%d'),
        })
        self.assertFalse(RFQ.objects.filter(title='Past Deadline RFQ').exists())


class AdminRFQReviewTest(TestCase):

    def setUp(self):
        self.tc = TestClient()
        self.admin = make_admin()
        self.tc.login(email='admin@test.com', password='testpass123')

    def test_admin_can_view_rfq_list(self):
        response = self.tc.get('/forge/rfqs/')
        self.assertEqual(response.status_code, 200)

    def test_admin_can_approve_rfq(self):
        rfq = make_rfq(status=RFQ.SUBMITTED)
        response = self.tc.post(f'/forge/rfqs/{rfq.pk}/approve/')
        rfq.refresh_from_db()
        self.assertEqual(rfq.status, RFQ.BIDDING_OPEN)

    def test_admin_can_reject_rfq(self):
        rfq = make_rfq(status=RFQ.SUBMITTED)
        response = self.tc.post(f'/forge/rfqs/{rfq.pk}/reject/', {
            'rejection_reason': 'Insufficient specification detail.'
        })
        rfq.refresh_from_db()
        self.assertEqual(rfq.status, RFQ.REJECTED)

    def test_rejection_saves_reason(self):
        rfq = make_rfq(status=RFQ.SUBMITTED)
        self.tc.post(f'/forge/rfqs/{rfq.pk}/reject/', {
            'rejection_reason': 'Missing material specification.'
        })
        rfq.refresh_from_db()
        self.assertIn('Missing material', rfq.rejection_reason)


class VendorBiddingTest(TestCase):

    def setUp(self):
        self.tc = TestClient()
        self.vendor_user = make_vendor(email='vendor@test.com', verified=True)
        self.rfq = make_rfq(status=RFQ.BIDDING_OPEN)
        self.tc.login(email='vendor@test.com', password='testpass123')

    def test_vendor_can_view_open_rfq(self):
        response = self.tc.get(f'/vendor/rfqs/{self.rfq.pk}/bid/')
        self.assertEqual(response.status_code, 200)

    def test_vendor_can_submit_bid(self):
        response = self.tc.post(f'/vendor/rfqs/{self.rfq.pk}/bid/', {
            'price': '150000.00',
            'timeline_days': 14,
            'notes': 'Full QC included.',
        })
        self.assertTrue(Bid.objects.filter(
            rfq=self.rfq, vendor=self.vendor_user
        ).exists())

    def test_vendor_cannot_bid_twice_on_same_rfq(self):
        Bid.objects.create(
            rfq=self.rfq, vendor=self.vendor_user,
            price=Decimal('150000'), timeline_days=14,
        )
        response = self.tc.post(f'/vendor/rfqs/{self.rfq.pk}/bid/', {
            'price': '140000.00',
            'timeline_days': 10,
        })
        self.assertEqual(Bid.objects.filter(rfq=self.rfq, vendor=self.vendor_user).count(), 1)

    def test_vendor_cannot_bid_on_closed_rfq(self):
        closed_rfq = make_rfq(status=RFQ.BIDDING_CLOSED)
        response = self.tc.post(f'/vendor/rfqs/{closed_rfq.pk}/bid/', {
            'price': '100000',
            'timeline_days': 10,
        })
        self.assertFalse(Bid.objects.filter(rfq=closed_rfq, vendor=self.vendor_user).exists())


class AdminBidSelectionTest(TestCase):

    def setUp(self):
        self.tc = TestClient()
        self.admin = make_admin()
        self.rfq = make_rfq(status=RFQ.BIDDING_OPEN)
        self.vendor = make_vendor()
        self.bid = make_bid(rfq=self.rfq, vendor=self.vendor, price=Decimal('150000'))
        self.tc.login(email='admin@test.com', password='testpass123')

    def test_admin_can_view_bids(self):
        response = self.tc.get(f'/forge/rfqs/{self.rfq.pk}/bids/')
        self.assertEqual(response.status_code, 200)

    def test_admin_can_select_bid(self):
        response = self.tc.post(
            f'/forge/rfqs/{self.rfq.pk}/select-bid/{self.bid.pk}/',
            {
                'forge_margin_percentage': '15',
                'final_price': '172500.00',
                'deposit_percentage': '30',
                'admin_notes': 'Best vendor selected.',
            }
        )
        self.bid.refresh_from_db()
        self.assertEqual(self.bid.status, Bid.SELECTED)

    def test_selecting_bid_creates_quote(self):
        self.tc.post(
            f'/forge/rfqs/{self.rfq.pk}/select-bid/{self.bid.pk}/',
            {
                'forge_margin_percentage': '15',
                'final_price': '172500.00',
                'deposit_percentage': '30',
                'admin_notes': 'Best vendor selected.',
            }
        )
        self.assertTrue(Quote.objects.filter(rfq=self.rfq).exists())

    def test_selecting_bid_marks_others_not_selected(self):
        vendor2 = make_vendor(email='v2@test.com')
        bid2 = make_bid(rfq=self.rfq, vendor=vendor2, price=Decimal('200000'))
        self.tc.post(
            f'/forge/rfqs/{self.rfq.pk}/select-bid/{self.bid.pk}/',
            {
                'forge_margin_percentage': '0',
                'final_price': '150000.00',
                'deposit_percentage': '30',
                'admin_notes': 'Selected.',
            }
        )
        bid2.refresh_from_db()
        self.assertEqual(bid2.status, Bid.NOT_SELECTED)


class QuoteAndOrderTest(TestCase):

    def setUp(self):
        self.tc = TestClient()
        self.client_user = make_client(email='client@test.com', verified=True)
        self.bid = make_bid(rfq=make_rfq(client=self.client_user, status=RFQ.BIDDING_OPEN))
        self.quote = make_quote(rfq=self.bid.rfq, bid=self.bid, final_price=Decimal('172500'))
        # Set RFQ to QUOTE_SENT so client can accept
        self.bid.rfq.status = RFQ.QUOTE_SENT
        self.bid.rfq.save()
        self.tc.login(email='client@test.com', password='testpass123')

    def test_client_can_view_quote(self):
        response = self.tc.get(f'/client/rfq/{self.bid.rfq.pk}/quote/')
        self.assertEqual(response.status_code, 200)

    def test_client_accepting_quote_creates_order(self):
        self.tc.post(f'/client/rfq/{self.bid.rfq.pk}/accept/')
        self.assertTrue(Order.objects.filter(quote=self.quote).exists())

    def test_order_deposit_uses_quote_deposit_percentage(self):
        self.tc.post(f'/client/rfq/{self.bid.rfq.pk}/accept/')
        order = Order.objects.get(quote=self.quote)
        expected_deposit = Decimal('172500') * Decimal('30') / 100
        self.assertAlmostEqual(float(order.deposit_amount), float(expected_deposit), places=2)

    def test_order_created_with_pending_payment_status(self):
        self.tc.post(f'/client/rfq/{self.bid.rfq.pk}/accept/')
        order = Order.objects.get(quote=self.quote)
        self.assertEqual(order.status, Order.PENDING_PAYMENT)
