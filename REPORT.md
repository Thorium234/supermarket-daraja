# REPORT.md

## System Overview
This project has been refactored from a monolithic Django app into a cleaner, production-oriented structure while preserving existing shopping, checkout, payment, receipt, and dashboard features.

Key outcomes:
- Added service/repository architecture for catalog logic.
- Added modular API layer with JWT auth and rate limiting.
- Added category and review domain models.
- Added Unsplash-based image service with cache + deterministic fallback.
- Added customer registration and customer dashboard.
- Strengthened configuration and endpoint security patterns.
- Added unit/integration/frontend smoke tests.

## Full System Analysis (Before Refactor)
### Architectural Issues
- Large `product/views.py` mixed UI rendering, business rules, persistence, and API-like behavior.
- No clear service/repository boundaries.
- Domain logic duplicated across templates/views.

### Performance Bottlenecks
- Limited use of query optimization for list endpoints.
- Missing structured pagination/sorting/filtering in API layer.
- Repeated expensive logic in view/template path.

### Folder Structure Issues
- Backend concerns were concentrated in views modules.
- No dedicated `core/` modules for cross-cutting concerns (auth, rate limit, response format).

### Security Vulnerabilities / Risks
- Hardcoded secrets and credentials in settings.
- No API token strategy for stateless auth.
- No centralized rate limiting.
- No unified API error envelope.

### Duplicate Logic / Naming / Scalability
- Similar list/filter logic duplicated in web behavior.
- Weak separation of web UI logic vs API contract logic.
- Scalability constraints from tight coupling and missing layered architecture.

### Missing Best Practices
- Missing service layer and repository abstraction.
- Missing explicit API tests for auth + ordering workflows.
- Missing category and review domain entities for marketplace behavior.

## Architecture Diagram Explanation (Text-Based)

```
[Client Web UI / API Consumers]
          |
          v
[URL Router]
  |-- Web Views (Django templates)
  |-- API Controllers (product/api/views.py)
          |
          v
[Service Layer]
  |-- ProductCatalogService
  |-- UnsplashImageService
          |
          v
[Repository Layer]
  |-- ProductRepository (query composition, sorting, annotations)
          |
          v
[Domain Models / ORM]
  |-- Product, Category, ProductReview, Order, OrderItem, Customer, Payment
          |
          v
[Database + Cache]
  |-- SQLite (current)
  |-- Django cache (LocMem; Redis-ready design)

Cross-cutting:
[core/jwt_auth.py] [core/rate_limit.py] [core/responses.py] [core/middleware.py]
```

## Folder Structure Explanation

Refactored additions:
- `supermarket/supermarket/core/`
  - `jwt_auth.py` (JWT creation/validation + decorators)
  - `rate_limit.py` (cache-backed API limiter)
  - `responses.py` (standard API envelopes + JSON parsing)
  - `middleware.py` (API exception handling + CORS headers)
- `supermarket/product/repositories.py`
  - query abstraction with filtering/sorting/annotations.
- `supermarket/product/services/`
  - `product_service.py` (catalog business logic)
  - `image_service.py` (Unsplash integration + caching + fallback)
- `supermarket/product/api/`
  - API controllers and dedicated API routes.
- `supermarket/product/templates/components/`
  - reusable `navbar`, `footer`, `button`, `modal` components.
- `supermarket/product/templates/product/components/`
  - reusable `product_card` component.

## Technology Stack
- Backend: Django 5.2
- ORM: Django ORM
- Auth: Django auth + JWT (PyJWT)
- Payments: M-Pesa integration (`django_daraja`)
- Async readiness: Celery settings present
- Caching: Django cache (LocMem, Redis-compatible approach)
- Frontend: Django templates + Bootstrap + custom CSS
- Testing: Django TestCase (unit/integration/smoke)

## Database Schema Explanation
### Existing + Upgraded Core Models
- `Customer`
  - Added `user` one-to-one mapping for authenticated customer identity.
- `Product`
  - Added `image` and `category` relation.
  - Added index-friendly fields for listing performance.
- `Category` (new)
  - `name`, `slug`, activation flag, indexed lookup.
- `ProductReview` (new)
  - `product`, `customer`, `rating`, `comment`.
  - Unique constraint: one review per customer per product.
- `Order`/`OrderItem`
  - Indexed for status/date querying.

## API Endpoints Documentation
Base: `/api/`

### Authentication
- `POST /api/auth/register/`
  - Register customer + user, returns JWT.
- `POST /api/auth/login/`
  - Login and return JWT.

### Catalog
- `GET /api/products/`
  - Query params:
    - `search`
    - `category` (slug)
    - `min_price`, `max_price`
    - `sort` (`price_asc`, `price_desc`, `newest`, `popularity`, `rating`, `name`)
    - `page`, `page_size`, `stock_only=1`
- `GET /api/products/<product_id>/`
  - Product detail + reviews.
- `GET /api/categories/`
  - Category list.

### Reviews
- `POST /api/products/<product_id>/reviews/` (JWT)
  - Create/update rating + comment.

### Orders
- `POST /api/orders/` (JWT)
  - Create order from item payload.
- `GET /api/orders/history/` (JWT)
  - Customer order history.

### Admin
- `POST /api/admin/products/` (JWT staff-only)
  - Create product.

## Authentication Flow Explanation
### Web
- Django session auth for template pages (`/accounts/login/`, customer register, dashboards).

### API (JWT)
1. Register/login to receive token.
2. Client sends `Authorization: Bearer <token>`.
3. `jwt_required` decorator validates token and injects `request.api_user`.
4. Staff-only endpoints enforce role check.

## Image Integration Explanation (Unsplash)
Implemented `UnsplashImageService`:
- Builds category-aware search keyword (`category -> keyword map`).
- Calls Unsplash Search API with optimized parameters.
- Caches image URL by keyword for 24 hours.
- Adds size/quality optimization in URL.
- Uses deterministic fallback image at:
  - `/static/product/img/fallback-product.svg`
- Uses uploaded local image first, Unsplash second, fallback last.

## Performance Optimizations Implemented
- Repository-level query composition + annotations.
- Pagination in catalog API.
- Sorting/filtering in database layer.
- `select_related` for key relations.
- Added DB indexes on high-frequency filter/sort fields.
- Caching for Unsplash fetch results.
- Lazy loading for product card images (`loading="lazy"`).

## Security Improvements Implemented
- JWT auth for API endpoints.
- Staff-only JWT guards for admin API.
- Rate limiting for auth/order/catalog API paths.
- Standardized API error responses (reduced leakage + consistency).
- API exception middleware and controlled JSON failures.
- CORS headers for API responses (including preflight support).
- Moved settings to env-driven patterns (with safe defaults) for credentials/secrets.
- Existing Django protections retained (ORM SQL injection safety, password hashing).

## Feature Upgrades Implemented
- Product categories (model + relations + admin support).
- Ratings & reviews (model + API endpoint).
- Product search/filter/sort/pagination API.
- Shopping cart/order logic extended via API order creation.
- Order history endpoint for authenticated customers.
- JWT-based API auth.
- Customer dashboard plus existing admin dashboard separation.
- Image enrichment via Unsplash + fallback.

## Refactored Codebase Structure (Summary)
- `supermarket/supermarket/core/*`
- `supermarket/product/repositories.py`
- `supermarket/product/services/*`
- `supermarket/product/api/*`
- `supermarket/product/templates/components/*`
- `supermarket/product/templates/product/components/product_card.html`
- updated domain models + migrations + tests.

## Tests Added
- `product/test_services.py` (service unit tests)
- `product/test_api.py` (API integration tests)
- `product/test_frontend.py` (critical page smoke tests)

Current result:
- `python manage.py test product payment -v 2` passes.

## Future Improvement Suggestions
1. Move from SQLite to PostgreSQL for production load + advanced indexing.
2. Add Redis as cache + rate limit backend for multi-instance deployments.
3. Add refresh tokens + token revocation list for JWT lifecycle hardening.
4. Add dedicated API serializers (DRF) for stricter schema contracts.
5. Split monolithic `product/views.py` web views into smaller controller modules.
6. Add asynchronous image prefetch job queue for Unsplash at product creation time.
7. Add observability stack (structured logging, tracing, metrics, Sentry).
8. Add CI pipeline for linting, tests, security scanning, and migration checks.

