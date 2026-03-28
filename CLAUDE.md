# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Iqtinaa Backend** — a Django REST Framework e-commerce API with JWT auth, product catalog, cart, orders, Stripe payments, and favorites.

## Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver

# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test accounts
python manage.py test cart

# Create database migrations after model changes
python manage.py makemigrations
```

## Architecture

### Custom User Model
`accounts.CustomUser` uses email (not username) for login. All Django auth references must use this model (`AUTH_USER_MODEL = 'accounts.CustomUser'`).

### App Structure
| App | Responsibility |
|-----|---------------|
| `accounts` | CustomUser, Profile, JWT auth, password reset via email |
| `products` | Product catalog with pagination (6/page), stock tracking |
| `cart` | Per-user cart (OneToOne), CartItem with stock validation |
| `order` | Orders created from cart at payment time, OrderItem captures price snapshot |
| `payments` | Stripe Payment Intent creation, cart-to-order conversion (`PaymentService`) |
| `webhooks` | Stripe webhook handler that finalizes orders after payment success |
| `favourites` | User product wish list |
| `store` | Django project settings, URL routing, env config (`keys.py`) |

### Payment Flow
1. `POST /api/payments/intent/` — validates cart stock, creates `Order` + `OrderItem` records, creates Stripe Payment Intent, returns `client_secret`
2. Frontend completes payment via Stripe
3. `POST /webhooks/stripe/` — receives `payment_intent.succeeded`, marks payment/order as paid, deducts product stock, clears cart (atomic transaction)

### Environment Variables
Loaded in `store/keys.py` via `environ`. Required vars in `.env`:
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`
- `FRONTEND_URL` (used for password reset email links)
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (Gmail SMTP)

### Key Design Decisions
- JWT tokens: access expires in 1 day, refresh in 7 days with rotation + blacklisting
- `PaymentService` (`payments/services.py`) uses MD5-based idempotency keys to prevent duplicate Stripe charges
- Webhook handler uses `@transaction.atomic` and checks existing payment/order status to prevent duplicate processing
- Products are only listed if `is_active=True` and `stock > 0`
- Cart is cleared only after successful webhook confirmation (not at payment intent creation)
