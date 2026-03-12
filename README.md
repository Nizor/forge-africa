# Forge Africa — Decentralized Manufacturing Platform

A Django + Jinja2 platform connecting manufacturing clients with a vendor network via a structured RFQ and bidding workflow.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL
- Git

### 1. Clone and set up environment

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your database credentials, SendGrid key, Paystack keys
```

### 3. Set up the database

```bash
# Create PostgreSQL database
createdb forge_africa

# Run Django migrations
python manage.py migrate

# Seed service categories
python manage.py seed_categories

# Create your first admin user
python manage.py create_admin --email admin@forgeafrica.com --password yourpassword --first-name Admin --last-name User
```

### 4. Run the development server

```bash
python manage.py runserver
```

Visit: http://localhost:8000

---

## 🗂️ Project Structure

```
forge_africa/
├── config/                  # Django settings, urls, wsgi
│   └── settings/
│       ├── base.py
│       ├── development.py
│       └── production.py
├── apps/
│   ├── accounts/            # Custom User model, auth, roles
│   ├── clients/             # Client dashboard, RFQ creation
│   ├── vendors/             # Vendor profiles, bidding
│   ├── rfqs/                # RFQ model, service categories
│   ├── bids/                # Bid submission and tracking
│   ├── quotes/              # Quote generation by admin
│   ├── orders/              # Order and deposit management
│   ├── payments/            # Paystack integration + webhooks
│   ├── notifications/       # Email + in-app notifications
│   └── forge_admin/         # Forge Africa staff interface
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS, JS, images
└── media/                   # User-uploaded files
```

---

## 👥 User Roles

| Role | Registration | Access |
|------|-------------|--------|
| **Client** | `/accounts/register/client/` | Submit RFQs, view quotes, pay deposits |
| **Vendor** | `/accounts/register/vendor/` | Browse RFQs, submit bids |
| **Admin** | `manage.py create_admin` | Full platform control |

---

## 🔄 Core Workflow

1. **Client** submits RFQ via `/client/rfq/new/`
2. **Admin** reviews at `/forge/rfqs/` → approves → RFQ broadcast to vendors
3. **Vendors** submit bids at `/vendor/rfqs/<id>/bid/`
4. **Admin** reviews bids, selects winner, sets final price → sends quote
5. **Client** receives email, reviews quote → accepts
6. **Client** pays deposit via Paystack
7. **Admin** coordinates work and updates status

---

## 🔑 Key URLs

```
/accounts/login/             — Login
/accounts/register/client/   — Client signup
/accounts/register/vendor/   — Vendor signup

/client/dashboard/           — Client home
/client/rfq/new/             — Submit new RFQ
/client/rfqs/                — All client RFQs

/vendor/dashboard/           — Vendor home
/vendor/rfqs/                — Available RFQs to bid on
/vendor/bids/                — Vendor's bid history

/forge/dashboard/            — Admin home
/forge/rfqs/                 — All RFQs management
/forge/vendors/              — Vendor management
/forge/settings/             — Platform settings

/payments/webhook/           — Paystack webhook (set in Paystack dashboard)
```

---

## 📧 Email Setup (SendGrid)

1. Create a free account at sendgrid.com
2. Create an API key with "Mail Send" permission
3. Add to `.env`: `SENDGRID_API_KEY=your_key`
4. Verify your sender domain/email in SendGrid

For development without SendGrid, set:
```bash
# In .env — leave SENDGRID_API_KEY blank
# Emails will print to the terminal console
```

---

## 💳 Paystack Setup

1. Create account at paystack.com
2. Get test keys from Dashboard → Settings → API Keys
3. Add to `.env`:
   ```
   PAYSTACK_SECRET_KEY=sk_test_xxx
   PAYSTACK_PUBLIC_KEY=pk_test_xxx
   ```
4. Set webhook URL in Paystack Dashboard:
   `https://yourdomain.com/payments/webhook/`

---

## 🌍 Deployment

```bash
# Set environment
DJANGO_SETTINGS_MODULE=config.settings.production

# Collect static files
python manage.py collectstatic

# Run with gunicorn
pip install gunicorn
gunicorn config.wsgi:application --workers 3
```

---

## 🛠️ Management Commands

```bash
# Seed service categories
python manage.py seed_categories

# Create admin user
python manage.py create_admin --email user@example.com --password secret
```

---

Built with ❤️ for African manufacturing.
