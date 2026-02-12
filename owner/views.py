from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from product.models import Category, Customer, Order, Product, ProductReview

from .forms import CategoryForm, OrderStatusForm, OwnerProductForm
from .services import OwnerAnalyticsService, OwnerQueryService


class OwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class DashboardOverviewView(OwnerRequiredMixin, TemplateView):
    template_name = "owner/dashboard_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = self.request.GET.get("period", "month")
        context.update(OwnerAnalyticsService.overview_metrics(period=period))
        context.update(OwnerAnalyticsService.chart_payloads())
        return context


class ProductListView(OwnerRequiredMixin, ListView):
    template_name = "owner/product_list.html"
    context_object_name = "products"
    paginate_by = 16

    def get_queryset(self):
        return OwnerQueryService.product_queryset(
            search=self.request.GET.get("q", "").strip(),
            category=self.request.GET.get("category", "").strip(),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = OwnerQueryService.categories_queryset()
        context["selected_category"] = self.request.GET.get("category", "")
        context["query"] = self.request.GET.get("q", "")
        return context


class ProductCreateView(OwnerRequiredMixin, CreateView):
    template_name = "owner/product_form.html"
    form_class = OwnerProductForm
    success_url = reverse_lazy("owner:product_list")

    def form_valid(self, form):
        messages.success(self.request, "Product created successfully.")
        return super().form_valid(form)


class ProductUpdateView(OwnerRequiredMixin, UpdateView):
    template_name = "owner/product_form.html"
    model = Product
    form_class = OwnerProductForm
    success_url = reverse_lazy("owner:product_list")

    def form_valid(self, form):
        messages.success(self.request, "Product updated successfully.")
        return super().form_valid(form)


class ProductDeleteView(OwnerRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy("owner:product_list")

    def post(self, request, *args, **kwargs):
        messages.warning(request, "Product deleted.")
        return super().post(request, *args, **kwargs)


class CategoryListCreateView(OwnerRequiredMixin, TemplateView):
    template_name = "owner/category_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = OwnerQueryService.categories_queryset()
        context["form"] = kwargs.get("form") or CategoryForm()
        return context

    def post(self, request, *args, **kwargs):
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category saved.")
            return redirect("owner:category_list")
        return self.render_to_response(self.get_context_data(form=form))


class OrderListView(OwnerRequiredMixin, ListView):
    template_name = "owner/order_list.html"
    context_object_name = "orders"
    paginate_by = 15

    def get_queryset(self):
        status = self.request.GET.get("status", "").strip()
        return OwnerQueryService.order_queryset(status=status)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_status"] = self.request.GET.get("status", "")
        context["status_choices"] = Order.STATUS_CHOICES
        return context


class OrderDetailView(OwnerRequiredMixin, DetailView):
    template_name = "owner/order_detail.html"
    model = Order
    context_object_name = "order"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_form"] = OrderStatusForm(instance=self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = OrderStatusForm(request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            messages.success(request, f"Order #{self.object.id} status updated.")
            return redirect("owner:order_detail", pk=self.object.pk)
        return self.render_to_response(self.get_context_data(status_form=form))


class CustomerListView(OwnerRequiredMixin, ListView):
    template_name = "owner/customer_list.html"
    context_object_name = "customers"
    paginate_by = 15

    def get_queryset(self):
        search = self.request.GET.get("q", "").strip()
        return OwnerQueryService.customer_queryset(search=search)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class CustomerDetailView(OwnerRequiredMixin, DetailView):
    template_name = "owner/customer_detail.html"
    model = Customer
    context_object_name = "customer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["orders"] = Order.objects.filter(customer=self.object).prefetch_related("items__product").order_by("-created_at")[:20]
        return context


class ReviewListView(OwnerRequiredMixin, ListView):
    template_name = "owner/review_list.html"
    context_object_name = "reviews"
    paginate_by = 20

    def get_queryset(self):
        queryset = ProductReview.objects.select_related("product", "customer").order_by("-created_at")
        product_id = self.request.GET.get("product", "").strip()
        if product_id.isdigit():
            queryset = queryset.filter(product_id=int(product_id))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.objects.order_by("name")[:200]
        context["selected_product"] = self.request.GET.get("product", "")
        return context


class ReviewDeleteView(OwnerRequiredMixin, View):
    def post(self, request, pk):
        review = get_object_or_404(ProductReview, pk=pk)
        review.delete()
        messages.warning(request, "Review deleted.")
        return HttpResponseRedirect(reverse("owner:review_list"))


class AnalyticsView(OwnerRequiredMixin, TemplateView):
    template_name = "owner/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(OwnerAnalyticsService.chart_payloads())
        context["top_products_table"] = OwnerAnalyticsService.top_products(limit=10)
        context["revenue_category_table"] = OwnerAnalyticsService.revenue_by_category(limit=10)
        return context
