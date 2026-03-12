#!/bin/bash
# ============================================================
# Forge Africa — Local Development Setup Script
# Run this once to set up your environment from scratch
# ============================================================
set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         FORGE AFRICA — Dev Setup         ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 1. Create virtual environment
echo "→ Creating virtual environment..."
python3 -m venv venv
echo "  ✓ Virtual environment created at ./venv"

# 2. Activate and install deps
echo ""
echo "→ Installing dependencies..."
venv/bin/pip install --upgrade pip --quiet
venv/bin/pip install -r requirements.txt --quiet
echo "  ✓ All packages installed"

# 3. Copy .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "  ✓ Created .env file from .env.example"
    echo "  ⚠️  IMPORTANT: Edit .env with your database credentials and API keys!"
else
    echo ""
    echo "  — .env already exists, skipping"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║           Next Steps                     ║"
echo "╠══════════════════════════════════════════╣"
echo "║                                          ║"
echo "║  1. Edit your .env file:                 ║"
echo "║     nano .env                            ║"
echo "║                                          ║"
echo "║  2. Create PostgreSQL database:          ║"
echo "║     createdb forge_africa                ║"
echo "║                                          ║"
echo "║  3. Run migrations:                      ║"
echo "║     venv/bin/python manage.py migrate    ║"
echo "║                                          ║"
echo "║  4. Seed service categories:             ║"
echo "║     venv/bin/python manage.py            ║"
echo "║       seed_categories                    ║"
echo "║                                          ║"
echo "║  5. Create admin user:                   ║"
echo "║     venv/bin/python manage.py            ║"
echo "║       createsuperuser                    ║"
echo "║     (use role=ADMIN in the shell after)  ║"
echo "║                                          ║"
echo "║  6. Start server:                        ║"
echo "║     venv/bin/python manage.py runserver  ║"
echo "║                                          ║"
echo "╚══════════════════════════════════════════╝"
echo ""
