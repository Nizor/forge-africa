from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse


def get_unread_notifications(user):
    """Global context helper - called from Jinja2 templates."""
    if not user or not user.is_authenticated:
        return []
    from .models import Notification
    return Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:10]


def create_notification(user, message, link=''):
    from .models import Notification
    Notification.objects.create(user=user, message=message, link=link)


def notify_admins(message, link=''):
    """Create an in-app notification for every active admin user."""
    from apps.accounts.models import User
    from .models import Notification
    admin_users = User.objects.filter(role=User.ADMIN, is_active=True)
    for admin_user in admin_users:
        Notification.objects.create(user=admin_user, message=message, link=link)


def send_email(to_email, subject, message, html_message=None):
    """
    Send email in a background thread so it never blocks a web request.
    SMTP connection hangs are completely isolated from the user experience.
    """
    import threading

    def _send():
        from django.core.mail import get_connection
        try:
            if settings.SENDGRID_API_KEY:
                port = getattr(settings, 'EMAIL_PORT', 2525)
                use_tls = port != 465
                use_ssl = port == 465
                connection = get_connection(
                    backend='django.core.mail.backends.smtp.EmailBackend',
                    host='smtp.sendgrid.net',
                    port=port,
                    username='apikey',
                    password=settings.SENDGRID_API_KEY,
                    use_tls=use_tls,
                    use_ssl=use_ssl,
                    fail_silently=False,
                    timeout=15,
                )
            else:
                connection = get_connection(
                    backend='django.core.mail.backends.console.EmailBackend',
                )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_message or message,
                connection=connection,
                fail_silently=False,
            )
            print(f'[EMAIL OK] Sent to {to_email}: {subject}')
        except Exception as e:
            print(f'[EMAIL ERROR] Failed to send to {to_email}: {e}')

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


def send_verification_email(user, request):
    verify_url = request.build_absolute_uri(
        reverse('accounts:verify_email', kwargs={'token': user.verification_token})
    )
    subject = 'Verify your Forge Africa account'
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #E85D04; padding: 20px; text-align: center;">
            <h1 style="color: white; margin: 0;">FORGE AFRICA</h1>
        </div>
        <div style="padding: 30px; background: #f9f9f9;">
            <h2>Welcome, {user.first_name}!</h2>
            <p>Thanks for registering on Forge Africa. Please verify your email address to activate your account.</p>
            <a href="{verify_url}" style="display: inline-block; background: #E85D04; color: white;
               padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: bold; margin: 20px 0;">
                Verify Email Address
            </a>
            <p style="color: #888; font-size: 13px;">If you didn't create an account, ignore this email.</p>
        </div>
    </div>
    """
    send_email(user.email, subject, f'Verify your account: {verify_url}', html)


def notify_admin_new_rfq(rfq, request):
    subject = f'[Forge Africa] New RFQ Submitted: {rfq.short_id}'
    admin_url = request.build_absolute_uri(
        reverse('forge_admin:rfq_detail', kwargs={'pk': rfq.pk})
    )
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #1A1A2E; padding: 20px; text-align: center;">
            <h1 style="color: #E85D04; margin: 0;">FORGE AFRICA ADMIN</h1>
        </div>
        <div style="padding: 30px;">
            <h2>New RFQ Submitted</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; font-weight: bold;">RFQ ID:</td><td>{rfq.short_id}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Title:</td><td>{rfq.title}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Client:</td><td>{rfq.client.get_full_name()} ({rfq.client.email})</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Category:</td><td>{rfq.category.name}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Deadline:</td><td>{rfq.deadline}</td></tr>
            </table>
            <a href="{admin_url}" style="display: inline-block; background: #E85D04; color: white;
               padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: bold; margin: 20px 0;">
                Review RFQ
            </a>
        </div>
    </div>
    """
    send_email(settings.ADMIN_EMAIL, subject, f'New RFQ {rfq.short_id} submitted. Review at {admin_url}', html)
    notify_admins(
        f'📋 New RFQ submitted: {rfq.short_id} — {rfq.title} by {rfq.client.get_full_name()}',
        f'/forge/rfqs/{rfq.pk}/'
    )


def notify_client_rfq_approved(rfq):
    subject = f'Your RFQ {rfq.short_id} is under review by our vendor network'
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #E85D04; padding: 20px; text-align: center;">
            <h1 style="color: white; margin: 0;">FORGE AFRICA</h1>
        </div>
        <div style="padding: 30px; background: #f9f9f9;">
            <h2>Great news, {rfq.client.first_name}!</h2>
            <p>Your RFQ <strong>{rfq.short_id} — {rfq.title}</strong> has been approved and is now open for bidding in our vendor network.</p>
            <p>You will be notified as soon as we have a curated quote ready for you to review.</p>
            <p style="color: #888; font-size: 13px;">Forge Africa — Building the Backbone of African Manufacturing</p>
        </div>
    </div>
    """
    send_email(rfq.client.email, subject, f'Your RFQ {rfq.short_id} is approved and in bidding.', html)
    create_notification(rfq.client, f'Your RFQ {rfq.short_id} has been approved and sent to vendors for bidding.', f'/client/rfq/{rfq.pk}/')


def notify_client_rfq_rejected(rfq):
    subject = f'Update on your RFQ {rfq.short_id}'
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #E85D04; padding: 20px; text-align: center;">
            <h1 style="color: white; margin: 0;">FORGE AFRICA</h1>
        </div>
        <div style="padding: 30px; background: #f9f9f9;">
            <h2>Update on RFQ {rfq.short_id}</h2>
            <p>Unfortunately, your RFQ <strong>{rfq.title}</strong> could not be processed at this time.</p>
            <div style="background: #fff3cd; border-left: 4px solid #E85D04; padding: 15px; margin: 15px 0;">
                <strong>Reason:</strong> {rfq.rejection_reason}
            </div>
            <p>You're welcome to submit a revised RFQ with the feedback above. Our team is happy to help.</p>
        </div>
    </div>
    """
    send_email(rfq.client.email, subject, f'RFQ {rfq.short_id} update: {rfq.rejection_reason}', html)
    create_notification(rfq.client, f'Your RFQ {rfq.short_id} was not approved. Reason: {rfq.rejection_reason[:100]}', f'/client/rfq/{rfq.pk}/')


def notify_vendors_new_rfq(rfq, vendors):
    """Email all vendors in the RFQ's service category."""
    for vendor_user in vendors:
        subject = f'[Forge Africa] New RFQ Available: {rfq.category.name}'
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1A1A2E; padding: 20px; text-align: center;">
                <h1 style="color: #E85D04; margin: 0;">FORGE AFRICA</h1>
                <p style="color: #ccc; margin: 5px 0;">Vendor Network</p>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <h2>New RFQ Available — {rfq.category.name}</h2>
                <p>Hello {vendor_user.first_name}, a new request matching your service category is available for bidding.</p>
                <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px;">
                    <tr><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #eee;">Title:</td><td style="padding: 10px; border-bottom: 1px solid #eee;">{rfq.title}</td></tr>
                    <tr><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #eee;">Category:</td><td style="padding: 10px; border-bottom: 1px solid #eee;">{rfq.category.name}</td></tr>
                    <tr><td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #eee;">Quantity:</td><td style="padding: 10px; border-bottom: 1px solid #eee;">{rfq.quantity}</td></tr>
                    <tr><td style="padding: 10px; font-weight: bold;">Deadline:</td><td style="padding: 10px;">{rfq.deadline}</td></tr>
                </table>
                <a href="{settings.SITE_URL}/vendor/rfqs/{rfq.pk}/bid/" style="display: inline-block; background: #E85D04; color: white;
                   padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: bold; margin: 20px 0;">
                    View & Submit Bid
                </a>
                {f'<p style="color: #e85d04; font-weight: bold;">⏰ Bidding closes: {rfq.bidding_deadline}</p>' if rfq.bidding_deadline else ''}
            </div>
        </div>
        """
        send_email(vendor_user.email, subject, f'New RFQ available for bidding: {rfq.title}', html)
        create_notification(vendor_user, f'New RFQ available: {rfq.title} ({rfq.category.name})', f'/vendor/rfqs/{rfq.pk}/bid/')


def notify_client_quote_ready(rfq):
    subject = f'Your quote is ready — RFQ {rfq.short_id}'
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #E85D04; padding: 20px; text-align: center;">
            <h1 style="color: white; margin: 0;">FORGE AFRICA</h1>
        </div>
        <div style="padding: 30px; background: #f9f9f9;">
            <h2>Your Quote is Ready! 🎉</h2>
            <p>Hello {rfq.client.first_name}, we've reviewed all bids for your project <strong>{rfq.title}</strong> and selected the best quote for you.</p>
            <p>Log in to your dashboard to review the quote and accept it to proceed.</p>
            <a href="{settings.SITE_URL}/client/rfq/{rfq.pk}/quote/" style="display: inline-block; background: #E85D04; color: white;
               padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: bold; margin: 20px 0;">
                Review Your Quote
            </a>
            <p style="color: #888; font-size: 13px;">Forge Africa — Building the Backbone of African Manufacturing</p>
        </div>
    </div>
    """
    send_email(rfq.client.email, subject, f'Your quote for RFQ {rfq.short_id} is ready. Login to review.', html)
    create_notification(rfq.client, f'Your quote for {rfq.short_id} is ready. Click to review and accept.', f'/client/rfq/{rfq.pk}/quote/')


def notify_deposit_paid(order):
    rfq = order.rfq
    vendor = rfq.quote.selected_bid.vendor

    # --- Client: payment confirmed ---
    send_email(
        rfq.client.email,
        f'Payment confirmed — RFQ {rfq.short_id}',
        f'Your deposit of ₦{order.deposit_amount:,.2f} has been confirmed. Your project is now in progress!',
        html_message=f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #E85D04; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">FORGE AFRICA</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <h2>Payment Confirmed ✅</h2>
                <p>Hello {rfq.client.first_name}, your deposit of <strong>₦{order.deposit_amount:,.2f}</strong>
                for project <strong>{rfq.title}</strong> has been received.</p>
                <p>Your vendor has been notified and will commence work shortly.</p>
                <div style="background: white; border-left: 4px solid #E85D04; padding: 15px; margin: 15px 0;">
                    <strong>RFQ:</strong> {rfq.short_id}<br>
                    <strong>Balance due on completion:</strong> ₦{order.balance_due:,.2f}
                </div>
                <a href="{settings.SITE_URL}/client/orders/" style="display: inline-block; background: #E85D04; color: white;
                   padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: bold; margin: 20px 0;">
                    View Your Order
                </a>
            </div>
        </div>
        """
    )
    create_notification(
        rfq.client,
        f'✅ Payment confirmed! ₦{order.deposit_amount:,.2f} deposit received for {rfq.short_id}. Your vendor is starting work.',
        f'/client/orders/'
    )

    # --- Vendor: work order notification ---
    send_email(
        vendor.email,
        f'[Forge Africa] Work Order — {rfq.short_id}: Client deposit received, please commence',
        f'The client has paid their deposit for {rfq.title}. Please commence work.',
        html_message=f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1A1A2E; padding: 20px; text-align: center;">
                <h1 style="color: #E85D04; margin: 0;">FORGE AFRICA</h1>
                <p style="color: #ccc; margin: 5px 0 0;">Work Order</p>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <h2>🚀 Deposit Received — Please Commence Work</h2>
                <p>Hello {vendor.first_name}, the client has completed their deposit payment for the following project.
                You may now begin work.</p>
                <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; margin: 15px 0;">
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px; font-weight: bold; width: 40%;">RFQ Reference:</td>
                        <td style="padding: 10px;">{rfq.short_id}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px; font-weight: bold;">Project:</td>
                        <td style="padding: 10px;">{rfq.title}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px; font-weight: bold;">Category:</td>
                        <td style="padding: 10px;">{rfq.category.name}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px; font-weight: bold;">Quantity:</td>
                        <td style="padding: 10px;">{rfq.quantity} unit(s)</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px; font-weight: bold;">Your Bid Price:</td>
                        <td style="padding: 10px; color: #16a34a; font-weight: bold;">₦{rfq.quote.selected_bid.price:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; font-weight: bold;">Client Deadline:</td>
                        <td style="padding: 10px; color: #E85D04;">{rfq.deadline.strftime('%d %b %Y')}</td>
                    </tr>
                </table>
                <div style="background: #fff3cd; border-left: 4px solid #E85D04; padding: 15px; margin: 15px 0;">
                    <strong>Important:</strong> Please log in to your vendor dashboard to view the full project
                    details and update your progress. Contact Forge Africa if you have any questions.
                </div>
                <a href="{settings.SITE_URL}/vendor/orders/" style="display: inline-block; background: #E85D04; color: white;
                   padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: bold; margin: 20px 0;">
                    Go to Vendor Dashboard
                </a>
            </div>
        </div>
        """
    )
    create_notification(
        vendor,
        f'🚀 Work Order: Deposit received for {rfq.short_id} — {rfq.title}. Please commence work.',
        f'/vendor/orders/'
    )

    # --- Admin: in-app + email ---
    send_email(
        settings.ADMIN_EMAIL,
        f'[Forge Africa] Deposit received — {rfq.short_id}',
        f'Client {rfq.client.get_full_name()} paid ₦{order.deposit_amount:,.2f} for {rfq.title}. Vendor {vendor.get_full_name()} has been notified to start work.'
    )
    notify_admins(
        f'💰 Deposit paid: {rfq.client.get_full_name()} paid ₦{order.deposit_amount:,.2f} for {rfq.short_id}. Vendor notified to start work.',
        f'/forge/rfqs/{rfq.pk}/'
    )
