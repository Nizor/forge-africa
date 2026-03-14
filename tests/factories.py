"""
Shared test factories for creating test data consistently across all test modules.
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from apps.accounts.models import User
from apps.rfqs.models import RFQ, ServiceCategory
from apps.bids.models import Bid
from apps.quotes.models import Quote
from apps.orders.models import Order
from apps.vendors.models import VendorProfile


def make_category(name='Metal Fabrication', slug='metal-fabrication'):
    return ServiceCategory.objects.get_or_create(
        slug=slug,
        defaults={'name': name, 'icon': '🔧', 'is_active': True}
    )[0]


def make_client(email='client@test.com', verified=True):
    return User.objects.create_user(
        email=email,
        password='testpass123',
        first_name='Test',
        last_name='Client',
        role=User.CLIENT,
        is_verified=verified,
    )


def make_vendor(email='vendor@test.com', verified=True):
    user = User.objects.create_user(
        email=email,
        password='testpass123',
        first_name='Test',
        last_name='Vendor',
        role=User.VENDOR,
        is_verified=verified,
    )
    cat = make_category()
    VendorProfile.objects.create(
        user=user,
        company_name='Test Manufacturing Co.',
        phone='08012345678',
        address='1 Test Street',
        city='Lagos',
        state='Lagos',
        is_verified=True,
    )
    user.vendor_profile.service_categories.add(cat)
    return user


def make_admin(email='admin@test.com'):
    return User.objects.create_user(
        email=email,
        password='testpass123',
        first_name='Admin',
        last_name='User',
        role=User.ADMIN,
        is_staff=True,
        is_verified=True,
    )


def make_rfq(client=None, status=RFQ.SUBMITTED, category=None):
    if client is None:
        client = make_client(email=f'client_{uuid.uuid4().hex[:6]}@test.com')
    if category is None:
        category = make_category()
    return RFQ.objects.create(
        client=client,
        title='Test RFQ — 500 Steel Brackets',
        description='Need 500 stainless steel L-brackets for furniture assembly.',
        category=category,
        quantity=500,
        materials='Stainless Steel',
        deadline=date.today() + timedelta(days=30),
        status=status,
    )


def make_bid(rfq=None, vendor=None, price=Decimal('150000.00'), timeline_days=14):
    if rfq is None:
        rfq = make_rfq(status=RFQ.BIDDING_OPEN)
    if vendor is None:
        vendor = make_vendor(email=f'vendor_{uuid.uuid4().hex[:6]}@test.com')
    return Bid.objects.create(
        rfq=rfq,
        vendor=vendor,
        price=price,
        timeline_days=timeline_days,
        notes='We can deliver on time with full QC.',
        status=Bid.SUBMITTED,
    )


def make_quote(rfq=None, bid=None, final_price=None, deposit_pct=30, margin_pct=Decimal('15.00')):
    if bid is None:
        bid = make_bid()
    if rfq is None:
        rfq = bid.rfq
    if final_price is None:
        final_price = bid.price * (1 + margin_pct / 100)
    bid.status = Bid.SELECTED
    bid.save()
    return Quote.objects.create(
        rfq=rfq,
        selected_bid=bid,
        final_price=final_price,
        forge_margin_percentage=margin_pct,
        deposit_percentage=deposit_pct,
        admin_notes='Best vendor selected for your project.',
    )


def make_order(quote=None):
    if quote is None:
        quote = make_quote()
    total = quote.final_price
    dep_pct = quote.deposit_percentage
    deposit = (Decimal(dep_pct) / 100) * total
    return Order.objects.create(
        quote=quote,
        deposit_percentage=dep_pct,
        deposit_amount=deposit,
        total_amount=total,
        balance_due=total - deposit,
        status=Order.PENDING_PAYMENT,
    )
