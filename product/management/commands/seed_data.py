from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random

from product.models import Shelf, Product, Customer, Order, OrderItem
from payment.models import Payment, StockDeductionLog


class Command(BaseCommand):
    help = "Seed database with shelves, products, customers, orders, payments, and stock deduction logs"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Seeding database..."))

        # 1. Shelves
        shelves = []
        shelf_names = ["Aisle 1", "Aisle 2", "Aisle 3", "Cold Storage", "Drinks Section"]
        for name in shelf_names:
            shelf, _ = Shelf.objects.get_or_create(
                name=name,
                defaults={
                    "location": f"Location {name}",
                    "description": f"Shelf for {name}",
                },
            )
            shelves.append(shelf)
        self.stdout.write(self.style.SUCCESS(f"✔ Created {len(shelves)} shelves"))

        # 2. Products
        products = []
        product_data = [
            ("Bread", "Fresh baked bread", "111111", 50, 100),
            ("Milk", "500ml packet", "222222", 60, 200),
            ("Eggs", "Tray of 30", "333333", 350, 50),
            ("Sugar", "2kg packet", "444444", 280, 120),
            ("Rice", "5kg bag", "555555", 650, 75),
        ]
        for name, desc, barcode, price, stock in product_data:
            product, _ = Product.objects.get_or_create(
                name=name,
                defaults={
                    "description": desc,
                    "barcode": barcode,
                    "price": Decimal(price),
                    "stock": stock,
                    "shelf": random.choice(shelves),
                },
            )
            products.append(product)
        self.stdout.write(self.style.SUCCESS(f"✔ Created {len(products)} products"))

        # 3. Customers
        customers = []
        customer_data = [
            ("John Doe", "0712345678", "john@example.com"),
            ("Mary Jane", "0722334455", "mary@example.com"),
            ("Guest", "0700111222", None),
        ]
        for name, phone, email in customer_data:
            customer, _ = Customer.objects.get_or_create(
                phone_number=phone,
                defaults={"name": name, "email": email},
            )
            customers.append(customer)
        self.stdout.write(self.style.SUCCESS(f"✔ Created {len(customers)} customers"))

        # 4. Orders + Items + Payments + Stock Logs
        for i in range(3):
            customer = random.choice(customers)
            order = Order.objects.create(
                customer=customer,
                customer_name=customer.name or "Guest",
                status="PENDING",
                total_price=0,
            )

            total = Decimal("0.00")
            order_items = []
            for _ in range(random.randint(1, 3)):  # 1–3 items
                product = random.choice(products)
                qty = random.randint(1, 5)
                item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    price=product.price,
                )
                order_items.append(item)
                total += item.subtotal()
            order.total_price = total
            order.save()

            # Payment
            status = random.choice(["PENDING", "PAID", "FAILED"])
            payment = Payment.objects.create(
                order=order,
                amount=order.total_price,
                status=status,
                mpesa_receipt_no=f"T{random.randint(100000,999999)}",
                transaction_date=timezone.now(),
            )

            # Stock Deduction Logs + Actual stock changes
            for item in order_items:
                if status == "PAID":
                    # Deduct stock
                    if item.product.stock >= item.quantity:
                        item.product.stock -= item.quantity
                        item.product.save()

                    StockDeductionLog.objects.create(
                        product=item.product,
                        order=order,
                        payment=payment,
                        quantity=item.quantity,
                        action=StockDeductionLog.DEDUCT,
                        source=StockDeductionLog.AUTO,
                    )
                elif status in ["FAILED", "REFUNDED"] and random.choice([True, False]):
                    # Rollback (increase stock back)
                    item.product.stock += item.quantity
                    item.product.save()

                    StockDeductionLog.objects.create(
                        product=item.product,
                        order=order,
                        payment=payment,
                        quantity=item.quantity,
                        action=StockDeductionLog.ROLLBACK,
                        source=StockDeductionLog.AUTO,
                    )

        self.stdout.write(self.style.SUCCESS("✔ Created sample orders + payments + stock logs"))
        self.stdout.write(self.style.SUCCESS("🎉 Seeding complete!"))
