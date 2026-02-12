from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.db import transaction
from django.shortcuts import get_object_or_404

from supermarket.core.responses import api_success, api_error, parse_json_body
from supermarket.core.jwt_auth import create_access_token, jwt_required
from supermarket.core.rate_limit import rate_limit

from product.forms import CustomerRegistrationForm
from product.models import Product, Customer, Order, OrderItem, ProductReview, Category
from product.services.product_service import ProductCatalogService
from product.serializers import serialize_review


@csrf_exempt
@require_POST
@rate_limit(key_prefix="auth-register", limit=20, window_seconds=60)
def auth_register_api(request):
    payload = parse_json_body(request)
    if payload is None:
        return api_error("Invalid JSON", status=400)

    form = CustomerRegistrationForm(payload)
    if not form.is_valid():
        return api_error("Validation failed", status=422, errors=form.errors)

    user = form.save(commit=False)
    user.first_name = form.cleaned_data["first_name"]
    user.last_name = form.cleaned_data["last_name"]
    user.email = form.cleaned_data["email"]
    user.save()

    customer, _ = Customer.objects.get_or_create(
        phone_number=form.cleaned_data["phone_number"],
        defaults={
            "user": user,
            "name": f"{user.first_name} {user.last_name}".strip(),
            "email": user.email,
        },
    )
    if customer.user_id is None:
        customer.user = user
        customer.save(update_fields=["user"])

    token = create_access_token(user)
    return api_success(
        {
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
            },
        },
        message="Registration successful",
        status=201,
    )


@csrf_exempt
@require_POST
@rate_limit(key_prefix="auth-login", limit=30, window_seconds=60)
def auth_login_api(request):
    payload = parse_json_body(request)
    if payload is None:
        return api_error("Invalid JSON", status=400)

    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    if not username or not password:
        return api_error("Username and password are required", status=400)

    from django.contrib.auth import authenticate
    user = authenticate(username=username, password=password)
    if not user:
        return api_error("Invalid credentials", status=401)

    token = create_access_token(user)
    return api_success(
        {
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
            },
        },
        message="Login successful",
    )


@require_GET
@rate_limit(key_prefix="catalog", limit=120, window_seconds=60)
def product_list_api(request):
    search = (request.GET.get("search") or "").strip() or None
    category = (request.GET.get("category") or "").strip() or None
    sort = (request.GET.get("sort") or "newest").strip()

    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    page = request.GET.get("page", 1)
    page_size = request.GET.get("page_size", 12)

    try:
        min_price = float(min_price) if min_price else None
        max_price = float(max_price) if max_price else None
        page = int(page)
        page_size = min(max(int(page_size), 1), 50)
    except ValueError:
        return api_error("Invalid numeric query parameters", status=400)

    catalog = ProductCatalogService.list_products(
        search=search,
        category=category,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        page=page,
        page_size=page_size,
        stock_only=(request.GET.get("stock_only") == "1"),
    )
    return api_success(catalog)


@require_GET
def category_list_api(request):
    categories = Category.objects.filter(is_active=True).order_by("name")
    payload = [
        {"id": category.id, "name": category.name, "slug": category.slug}
        for category in categories
    ]
    return api_success({"items": payload})


@require_GET
@rate_limit(key_prefix="product-detail", limit=120, window_seconds=60)
def product_detail_api(request, product_id):
    product = get_object_or_404(Product.objects.select_related("category", "shelf"), id=product_id)
    image_url = product.image.url if product.image else None

    reviews_qs = product.reviews.select_related("customer").all()[:20]
    reviews = [serialize_review(review) for review in reviews_qs]

    payload = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": float(product.price),
        "discount_percentage": int(product.discount_percentage or 0),
        "discounted_price": float(product.discounted_price),
        "stock": product.stock,
        "barcode": product.barcode,
        "category": product.category.name if product.category else None,
        "image_url": image_url,
        "reviews": reviews,
    }
    return api_success(payload)


@csrf_exempt
@require_POST
@jwt_required()
@rate_limit(key_prefix="order-create", limit=30, window_seconds=60)
def order_create_api(request):
    payload = parse_json_body(request)
    if payload is None:
        return api_error("Invalid JSON", status=400)

    items = payload.get("items") or []
    if not isinstance(items, list) or not items:
        return api_error("'items' must be a non-empty list", status=400)

    customer = Customer.objects.filter(user=request.api_user).first()
    if not customer:
        return api_error("Customer profile not found", status=404)

    order_items = []
    total = 0
    for item in items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 1)
        try:
            quantity = int(quantity)
        except Exception:
            return api_error("Invalid quantity", status=400)
        if quantity <= 0:
            return api_error("Quantity must be greater than zero", status=400)

        product = Product.objects.filter(id=product_id).first()
        if not product:
            return api_error(f"Product {product_id} not found", status=404)
        if product.stock < quantity:
            return api_error(f"Insufficient stock for {product.name}", status=409)

        subtotal = product.discounted_price * quantity
        total += subtotal
        order_items.append((product, quantity, product.discounted_price))

    with transaction.atomic():
        order = Order.objects.create(customer=customer, total_price=total, status="PENDING")
        OrderItem.objects.bulk_create(
            [
                OrderItem(order=order, product=product, quantity=qty, price=price)
                for product, qty, price in order_items
            ]
        )

    return api_success({"order_id": order.id, "status": order.status, "total_price": float(order.total_price)}, message="Order created", status=201)


@require_GET
@jwt_required()
def order_history_api(request):
    customer = Customer.objects.filter(user=request.api_user).first()
    if not customer:
        return api_error("Customer profile not found", status=404)

    orders = Order.objects.filter(customer=customer).order_by("-created_at")[:50]
    data = [
        {
            "id": order.id,
            "status": order.status,
            "total_price": float(order.total_price),
            "created_at": order.created_at.isoformat(),
            "items_count": order.items.count(),
        }
        for order in orders
    ]
    return api_success({"items": data})


@csrf_exempt
@require_POST
@jwt_required()
def review_create_api(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    customer = Customer.objects.filter(user=request.api_user).first()
    if not customer:
        return api_error("Customer profile not found", status=404)

    payload = parse_json_body(request)
    if payload is None:
        return api_error("Invalid JSON", status=400)

    try:
        rating = int(payload.get("rating", 0))
    except ValueError:
        return api_error("Invalid rating", status=400)

    comment = (payload.get("comment") or "").strip()
    if rating < 1 or rating > 5:
        return api_error("Rating must be between 1 and 5", status=400)

    review, created = ProductReview.objects.update_or_create(
        product=product,
        customer=customer,
        defaults={"rating": rating, "comment": comment},
    )
    status = 201 if created else 200
    return api_success({"review_id": review.id, "rating": review.rating, "comment": review.comment}, status=status)


@csrf_exempt
@require_POST
@jwt_required(staff_only=True)
def admin_product_create_api(request):
    payload = parse_json_body(request)
    if payload is None:
        return api_error("Invalid JSON", status=400)

    name = (payload.get("name") or "").strip()
    if not name:
        return api_error("Product name is required", status=400)

    try:
        price = float(payload.get("price", 0))
        stock = int(payload.get("stock", 0))
        discount_percentage = int(payload.get("discount_percentage", 0))
    except ValueError:
        return api_error("Invalid price or stock", status=400)

    if price < 0 or stock < 0 or discount_percentage < 0 or discount_percentage > 90:
        return api_error("Price/stock must be non-negative and discount must be 0-90", status=400)

    category = None
    category_slug = payload.get("category")
    if category_slug:
        category = Category.objects.filter(slug=category_slug).first()

    product = Product.objects.create(
        name=name,
        description=(payload.get("description") or "").strip(),
        price=price,
        stock=stock,
        discount_percentage=discount_percentage,
        is_active=bool(payload.get("is_active", True)),
        barcode=(payload.get("barcode") or None),
        category=category,
    )
    return api_success({"id": product.id, "name": product.name}, message="Product created", status=201)
