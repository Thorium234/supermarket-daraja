# REPORT.md

## 1. System Overview
This platform is a Django-based, Jumia-style e-commerce system for supermarket operations and digital checkout (including M-Pesa).

Primary user roles:
- Customer: browse products, add to cart, checkout, pay, view receipts/order history.
- Owner/Seller: manage catalog, orders, customers, reviews, and analytics through a custom dashboard.
- Admin: platform-level governance via Django admin and staff controls.

Business domains currently implemented:
- Product catalog and categories
- Cart/checkout/order lifecycle
- Payment status integration (M-Pesa + callback handling)
- Receipt and verification flow
- Ratings and reviews
- Owner center analytics and management operations
- API endpoints with JWT authentication and rate limiting

## 2. Full System Analysis (Before and During Refactor)
### Architecture Issues Identified
- `product/views.py` was a monolith containing storefront, checkout, dashboard, and reporting logic.
- Cross-cutting concerns (API response format, rate limiting, auth middleware) were scattered or missing.
- Owner workflows were tightly coupled to general product app views.

### Security Issues Identified
- Hardcoded credentials/secrets in settings defaults.
- API error payloads exposed exception internals in all environments.
- Inconsistent permission boundaries for owner-only operations.
- Startup-time DB mutations from admin import side effects.

### Performance Issues Identified
- Repeated query patterns without centralized repository/service composition.
- Heavy list pages lacking consistent pagination/filter conventions in some views.
- Missing strategic indexes for high-frequency payment/order filters.

### Code Quality / Maintainability Issues Identified
- Duplicate/obsolete signal code and malformed `apps.py` content.
- Payment utility code referenced nonexistent model fields and invalid statuses.
- Mixed naming conventions and duplicated business rules across views/API.

## 3. Refactoring and Architecture Upgrades Implemented
### 3.1 Cleaner Layering
Introduced a clearer request flow:
`Request -> URL -> View/Controller -> Service -> Repository -> Model -> Response`

Implemented modules:
- `supermarket/core/`
  - `jwt_auth.py` (JWT creation/validation decorators)
  - `rate_limit.py` (cache-backed request limiter)
  - `responses.py` (consistent API payload helpers)
  - `middleware.py` (central API exception/CORS handling)
- `product/services/`
  - `product_service.py` (catalog business logic)
  - `image_service.py` (Unsplash integration + caching + fallback)
- `product/repositories.py` (query composition, sorting, filtering, annotations)
- `product/api/` (API controllers and routes)
- `owner/` (new dedicated owner dashboard app)

### 3.2 Owner Dashboard (Custom Seller Center)
Created `owner` app with role-protected CBV pages:
- Dashboard Overview: KPIs, recent orders, low stock, chart datasets
- Product Management: list/search/filter, add/edit/delete, image upload, discount/stock/active controls
- Category Management: create/list categories
- Order Management: paginated order list, status filtering, per-order status updates
- Customer Management: customer list and purchase history view
- Review Moderation: list and delete inappropriate reviews
- Analytics: top products, revenue by category, charts

Access control:
- `OwnerRequiredMixin` enforces authenticated staff/superuser access.

### 3.3 Data Model Improvements
Enhanced schema in `product` domain:
- `Product`
  - Added `discount_percentage`
  - Added `is_active`
  - Added computed `discounted_price`
- `Order`
  - Expanded status flow: `PENDING`, `PAID`, `SHIPPED`, `DELIVERED`, `FAILED`, `CANCELLED`, `REFUNDED`
- Added persistent cart models:
  - `Cart`
  - `CartItem`
- Existing category/review models retained with constraints/indexes.

Payment schema improvements:
- Added indexes for payment status/order/date lookups.
- Added stock log indexes for operational reporting.

### 3.4 Business Logic Stabilization
- Fixed app initialization and signal wiring:
  - `product/apps.py`, `payment/apps.py` cleaned
  - startup DB side effects removed from admin import path
- Reworked `payment/signals.py` to use valid payment statuses and sync order state safely.
- Rewrote `payment/utils.py` to remove invalid field references and enforce idempotent stock operations.
- Updated checkout/cart and API order creation to use discounted prices and validate stock before order creation.

## 4. Django Apps and Folder Structure
Current app layout:
- `product/` -> storefront, cart/checkout/order/receipt, product domain, API + services/repositories
- `payment/` -> payment initiation, callback handling, payment models/tasks/utilities
- `owner/` -> seller-center style management dashboard (CBV-based)
- `supermarket/` -> project config + shared core modules

Notable structure additions:
- `owner/templates/owner/*`
- `product/templates/product/components/product_card.html`
- `product/templates/components/*` (reusable navbar/footer/button/modal)
- `product/serializers.py` (lightweight serializer helpers)

## 5. Database Structure (Current)
Core entities and relationships:
- User (Django auth)
  - one-to-one optional with `Customer`
- Customer
  - has many `Order`
  - has one `Cart`
  - has many `ProductReview`
- Category
  - has many `Product`
- Product
  - belongs to optional `Category`
  - has many `OrderItem`, `ProductReview`, `CartItem`
- Cart
  - belongs to one `Customer`
  - has many `CartItem`
- Order
  - belongs to optional `Customer`
  - has many `OrderItem`
  - has many `Payment`
- Payment
  - belongs to `Order`
- ProductReview
  - belongs to `Product` and `Customer`
  - unique constraint `(product, customer)`

Optimization measures:
- Added/retained indexes for product listing, order timelines/statuses, payment lifecycle queries.
- Foreign keys and related names normalized for query readability.

## 6. API Endpoints (Implemented)
Base path: `/api/`

Auth:
- `POST /api/auth/register/`
- `POST /api/auth/login/`

Catalog:
- `GET /api/products/` (pagination/filter/sort/search)
- `GET /api/products/<id>/`
- `GET /api/categories/`

Reviews:
- `POST /api/products/<id>/reviews/` (JWT required)

Orders:
- `POST /api/orders/` (JWT required)
- `GET /api/orders/history/` (JWT required)

Admin API:
- `POST /api/admin/products/` (JWT + staff required)

## 7. Authentication and Authorization Flow
### Web
- Session-based Django auth for storefront/customer and owner pages.
- Customer registration creates auth user + customer profile mapping.

### API
- JWT access tokens created at login/register.
- `Authorization: Bearer <token>` expected.
- Decorator-based guards:
  - `jwt_required()` for authenticated API actions
  - `jwt_required(staff_only=True)` for owner/admin API actions

### Owner Access
- `OwnerRequiredMixin` on all owner dashboard views.
- Non-staff users receive forbidden response for owner routes.

## 8. Owner Dashboard Explanation
Sections implemented:
- Overview: KPI cards, recent orders, low stock, trend charts
- Products: full CRUD with discount and activation controls
- Categories: category create/list management
- Orders: status filtering, pagination, per-order detail and status change
- Customers: customer list and order history
- Reviews: moderation delete action
- Analytics: top sellers and revenue by category

Operational behavior:
- Order progression now supports paid -> shipped -> delivered states.
- Low-stock visibility helps proactive restocking.
- Category/product analytics support merchandising decisions.

## 9. Unsplash Image Integration
Implemented via `product/services/image_service.py`:
- Maps product/category to relevant search keyword.
- Requests Unsplash dynamically using API key.
- Caches fetched URLs in Django cache to reduce API calls.
- Prioritizes uploaded product image; falls back to Unsplash URL; then static fallback SVG.
- Images rendered with lazy loading for frontend performance.

## 10. Performance Optimizations Implemented
- Centralized query composition in repository/service layers.
- Pagination added/retained on heavy listing pages and APIs.
- Query optimization with `select_related`/`prefetch_related` in owner/order/customer flows.
- Added indexes for product/order/payment high-frequency access paths.
- Unsplash result caching to reduce external API latency/cost.
- Lazy image loading in product cards.

## 11. Security Improvements Implemented
- API rate limiting for sensitive/high-traffic endpoints.
- JWT validation and staff-only endpoint protection.
- Secure cookie defaults tied to environment (`DEBUG` aware).
- Reduced host wildcard exposure in default `ALLOWED_HOSTS`.
- API middleware now avoids leaking exception details in production.
- Removed startup side effects and fragile signal logic.
- Continued use of Django ORM/CSRF/password hashing protections.

## 12. Testing and Validation
Added/updated tests:
- `owner/tests.py` (owner access control)
- `product/test_services.py`
- `product/test_api.py`
- `product/test_frontend.py`
- `payment/tests/test_callback.py` alignment

Validation executed:
- `../env/bin/python manage.py check` -> passed
- `../env/bin/python manage.py test owner product payment -v 2` -> passed

Note on local migration runtime:
- Applying migrations to the existing local `db.sqlite3` failed in this environment with `sqlite3.OperationalError: unable to open database file` during table remap, but migrations apply successfully in test DB (fresh in-memory database). This indicates a local DB-file/environment condition rather than migration definition failure.

## 13. Technology Stack
- Django 5.2
- SQLite (current), migration-ready for PostgreSQL
- Bootstrap + Django Templates for server-rendered UI
- Celery settings present for async tasks
- PyJWT for token authentication
- M-Pesa via `django_daraja`
- Cache layer (LocMem, Redis-compatible pattern)

## 14. Future Improvements
1. Split settings into `base.py/dev.py/prod.py` with strict env-only secrets.
2. Add full DRF serializers/viewsets and schema docs (OpenAPI).
3. Replace session cart with persistent `Cart/CartItem` integration for authenticated users.
4. Introduce PostgreSQL + Redis in deployment profile.
5. Add background jobs for image prefetch and analytics aggregation.
6. Add audit logs for owner actions (status changes, deletes, pricing changes).
7. Add CI/CD pipeline with linting, type checks, tests, and migration smoke tests.
8. Add observability stack (structured logging, metrics, tracing, error monitoring).
