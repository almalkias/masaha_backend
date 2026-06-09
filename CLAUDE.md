# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Iqtinaa Backend** — a Django REST Framework e-commerce API with JWT auth, product catalog, cart, orders, Stripe payments, coupons, and favourites.

- **Python:** 3.11
- **Django:** 5.1.6
- **DRF:** 3.15.2
- **Database:** SQLite3 (local) / Supabase PostgreSQL (production via `DATABASE_URL`)

## Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create migrations after model changes
python manage.py makemigrations

# Start development server
python manage.py runserver

# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test accounts
python manage.py test cart
python manage.py test payments

# Access Django shell
python manage.py shell

# Create superuser
python manage.py createsuperuser
```

## Environment Variables

Loaded in `store/keys.py` via `environ`. Required in `.env`:

```
SECRET_KEY=
DEBUG=
ALLOWED_HOSTS=
FRONTEND_URL=                  # Used for password reset email links
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
RESEND_API_KEY=                # Resend email service API key
TAX_RATE=0.15                  # Optional, defaults to 0.15 (15%)

# Production only
DATABASE_URL=                  # Supabase PostgreSQL connection string
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

## Architecture

### App Structure

| App | Responsibility |
|-----|----------------|
| `accounts` | CustomUser, Profile, JWT auth, password reset via Resend email |
| `products` | Product catalog with pagination (6/page) |
| `cart` | Per-user cart (OneToOne), CartItem (one entry per product, no quantity) |
| `order` | Orders created from cart at payment time, OrderItem captures price snapshot |
| `payments` | Stripe Payment Intent creation, cart-to-order conversion (`PaymentService`) |
| `webhooks` | Stripe webhook handler that finalizes orders after payment success |
| `favourites` | User product wish list |
| `coupons` | Discount coupon system (percentage/fixed) with per-user usage tracking |
| `store` | Django project settings, URL routing, env config (`keys.py`), language middleware |

### Custom User Model

`accounts.CustomUser` uses **email** (not username) for login. All Django auth references must use this model:

```python
AUTH_USER_MODEL = 'accounts.CustomUser'
```

- Never use `username` — it is set to `None` on the model
- Always filter users by `email`
- `Profile` is auto-created on user creation via `post_save` signal
- `Cart` is auto-created on user creation via `post_save` signal

### Internationalisation

- Default language: Arabic (`ar`). English (`en`) also supported.
- `store/middleware.py` — `LanguageMiddleware` reads the `X-Language` request header and activates the corresponding language per request.
- Locale files live under `locale/`.

### Payment Flow

1. `POST /api/payments/intent/` — validates cart, optionally applies coupon, creates `Order` + `OrderItem` records, creates Stripe PaymentIntent, returns `client_secret`
2. Frontend completes payment via Stripe JS SDK
3. `POST /webhooks/stripe/` — receives `payment_intent.succeeded`, marks payment/order as paid, records coupon usage, clears cart items (all in one `transaction.atomic` block)

### Coupon Flow

1. `POST /api/coupons/validate/` — validates coupon for the authenticated user, returns discount preview
2. Pass `coupon_code` in `POST /api/payments/intent/` request body to apply discount
3. Coupon usage is recorded only after webhook confirms successful payment (not at intent creation)

---

## Models Reference

### accounts.CustomUser
- `email` (EmailField, unique) — used as USERNAME_FIELD
- Inherits from AbstractUser; `username` field is removed

### accounts.Profile (OneToOne → CustomUser)
- `first_name`, `last_name` (CharField, max=100, blank)
- `country`, `city` (CharField, max=100, blank)
- `birth_date` (DateField, nullable)
- `image` (ImageField, `upload_to="profiles/"`, nullable)

### products.Product
- `name` (CharField, max=255)
- `description` (TextField, blank)
- `price` (DecimalField, 10 digits, 2 decimals)
- `image` (ImageField, `upload_to="products/"`, nullable)
- `is_active` (BooleanField, default=True)
- `created_at` (DateTimeField, auto_now_add)
- Listed only when `is_active=True`; ordered by `-id`
- `stock` field has been removed

### cart.Cart (OneToOne → CustomUser)
- `created_at` (DateTimeField, auto_now_add)

### cart.CartItem (ForeignKey → Cart)
- `product` (ForeignKey → Product, CASCADE)
- `unique_together = ("cart", "product")` — one entry per product, no quantity
- `quantity` field has been removed

### order.Order (ForeignKey → CustomUser)
- `coupon_code` (CharField, max=50, blank, default="")
- `discount_amount` (DecimalField, 10 digits, 2 decimals, default=0)
- `tax_amount` (DecimalField, 10 digits, 2 decimals, default=0)
- `total_price` (DecimalField, 10 digits, 2 decimals, default=0) — set at intent creation, never overwritten
- `status` (CharField, choices: pending/paid/cancelled, default="pending")
- `created_at` (DateTimeField, auto_now_add)

### order.OrderItem (ForeignKey → Order)
- `product` (ForeignKey → Product, CASCADE)
- `quantity` (PositiveIntegerField) — always 1
- `price` (DecimalField) — price snapshot at order creation time

### payments.Payment (ForeignKey → Order, ForeignKey → CustomUser)
- `stripe_payment_intent_id` (CharField, unique)
- `amount` (DecimalField)
- `currency` (CharField, default="usd")
- `status` (CharField, choices: pending/succeeded/failed)
- `created_at` (DateTimeField, auto_now_add)

### coupons.Coupon
- `code` (CharField, max=50, unique, db_index)
- `discount_type` (CharField, choices: "percentage"/"fixed")
- `discount_value` (DecimalField, 10 digits, 2 decimals)
- `max_uses` (PositiveIntegerField, nullable) — None = unlimited
- `times_used` (PositiveIntegerField, default=0)
- `is_active` (BooleanField, default=True)
- `expires_at` (DateTimeField, nullable)

### coupons.CouponUsage (ForeignKey → Coupon, ForeignKey → CustomUser)
- `used_at` (DateTimeField, auto_now_add)
- `unique_together = ("coupon", "user")` — one use per user

### favourites.Favourite (ForeignKey → CustomUser, ForeignKey → Product)
- `created_at` (DateTimeField, auto_now_add)
- `unique_together = ["user", "product"]`

---

## API Endpoints

### Accounts (`/api/accounts/`)

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | `/register/` | Public | Register with email + password |
| POST | `/login/` | Public | Get JWT tokens |
| POST | `/token/refresh/` | Public | Refresh access token |
| GET | `/profile/` | JWT | Fetch user profile |
| PUT | `/profile/` | JWT | Update profile (partial) |
| POST | `/logout/` | JWT | Blacklist refresh token |
| POST | `/change-password/` | JWT | Change password |
| POST | `/forgot-password/` | Public | Request password reset email (via Resend) |
| POST | `/reset-password-confirm/` | Public | Confirm reset (uid + token) |

### Products (`/api/products/`)

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/` | Public | List active products (paginated, 6/page) |
| GET | `/<int:pk>/` | Public | Product detail |

### Cart (`/api/cart/`)

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/` | JWT | Get cart with items |
| POST | `/add/` | JWT | Add product to cart |
| DELETE | `/<int:item_id>/delete/` | JWT | Remove item |
| DELETE | `/clear/` | JWT | Clear all cart items |

### Orders (`/api/orders/`)

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/` | JWT | List paid orders (ordered by `-created_at`) |

### Payments (`/api/payments/`)

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | `/intent/` | JWT | Create Stripe PaymentIntent (optionally with `coupon_code`) |

### Coupons (`/api/coupons/`)

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | `/validate/` | JWT | Validate coupon for current user (body: `{"code": "..."}`) |

### Favourites (`/api/favourites/`)

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/` | JWT | List user's favourited products |
| POST | `/<int:product_id>/` | JWT | Add product to favourites |
| DELETE | `/<int:product_id>/` | JWT | Remove product from favourites |

### Webhooks (`/webhooks/`)

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | `/stripe/` | Stripe signature | Handle `payment_intent.succeeded` |

---

## Key Design Decisions

- **JWT tokens:** access expires in 1 day, refresh in 7 days with rotation + blacklisting
- **Idempotency:** `PaymentService` uses MD5 hash of cart item IDs + total + coupon as Stripe idempotency key — prevents duplicate charges on retries
- **Webhook safety:** `transaction.atomic` + status checks on both `Payment` and `Order` prevent duplicate processing
- **Order creation timing:** `Order` is created at payment *intent* creation, not after payment confirmation
- **total_price immutability:** `Order.total_price` is set once by `PaymentService` (with discount applied) and never overwritten by the webhook
- **Cart clearing:** Only `CartItem` records are deleted after webhook confirmation — the `Cart` container is preserved (it is a persistent OneToOne with the user)
- **Coupon usage recording:** Only after successful payment webhook
- **Tax formula:** `tax = (subtotal - discount) * TAX_RATE`, quantized to 2 decimals
- **No stock tracking:** `stock` field removed from `Product`; products are listed whenever `is_active=True`
- **No quantity per cart item:** each product appears at most once in a cart; `OrderItem.quantity` is always 1

## Signals

| Signal | Sender | Effect |
|--------|--------|--------|
| `post_save` | `CustomUser` | Auto-creates `Profile` (`accounts/signals.py`) |
| `post_save` | `CustomUser` | Auto-creates `Cart` (`cart/signals.py`) |

## Custom Exceptions (`payments/exceptions.py`)

```python
class PaymentError(Exception)
class PaymentValidationError(PaymentError)   # e.g. empty cart, invalid coupon
class PaymentGatewayError(PaymentError)      # e.g. Stripe API failure
```

`Coupon.validate_for_user(user)` raises `PaymentValidationError` for invalid/expired/used coupons.

## Configuration Locations

| Concern | File |
|---------|------|
| Main Django settings | `store/settings.py` |
| REST/JWT/Stripe/Resend config | `store/keys.py` |
| URL routing | `store/urls.py` |
| Language middleware | `store/middleware.py` |
| Pagination | `REST_FRAMEWORK.PAGE_SIZE = 6` in `store/keys.py` |
| Tax rate | `TAX_RATE` env var, default `0.15` |
| CORS allowed origins | `http://localhost:3000`, `https://masaha-art.netlify.app` |

## Media & Static Files

- **Local development:** media served by Django from `MEDIA_ROOT = BASE_DIR / 'media'`
- **Production:** media stored on Cloudinary (`cloudinary_storage`); static files served by Whitenoise
- Product images: `upload_to="products/"`
- Profile images: `upload_to="profiles/"`
