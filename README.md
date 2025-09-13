
# Supermarket E-Commerce System with MPesa STK Push

## 🛒 Overview

This project is a **Django-based supermarket management and e-commerce system** with integrated **Safaricom MPesa Daraja API (STK Push)**.
It supports cashier-assisted checkout, self-service, and online ordering.
The system tracks inventory in real time, generates receipts, and provides a management dashboard for sales and stock flow analysis.

## 🛠 Core Workflows

### 1. Cashier Checkout

* Cashier selects products from shelves in the system.
* System sums up the total price automatically.
* Customer enters their phone number.
* STK Push is triggered → customer enters MPesa PIN.
* On success, stock reduces automatically and a receipt is generated.

### 2. E-Commerce Ordering

* Customer visits the website, selects products, and adds them to a cart.
* Customer checks out and enters their phone number.
* Payment is made via STK Push.
* Customer later collects the order at the supermarket.
* Receipt is issued digitally.

### 3. Self-Service Mode

* Customer in the supermarket selects products using the system directly.
* Customer pays via STK Push.
* Cashier sees the confirmed payment in the dashboard.
* Customer only needs to show their receipt (QR code or receipt number) at checkout.

### 4. Receipts

* Generated receipts contain product details, payment reference, and timestamp.
* Receipt numbers are randomized and recycled every 24 hours.
* Receipts can be downloaded as PDF, printed, or emailed.

## 📦 Inventory and Stock Management

* Products are arranged on shelves and grouped logically (e.g., `soap_shelf`, `milk_shelf`).
* Each product has a stock count.
* When stock is added (e.g., 200 soaps), it increases shelf stock.
* When products are sold (e.g., 20 soaps), stock decreases automatically.
* Dashboard alerts staff when stock falls below threshold.

## 📊 Dashboard and Reporting

* View all orders and payments.
* Track daily, weekly, and monthly revenue.
* See top-selling products and sales trends.
* Monitor stock flow with live updates.
* Export reports to **Excel, PDF, or CSV**.
* Print-ready sales and inventory summaries.

## 🔑 Features

* Product listing (name, barcode, price, stock).
* Multiple product selection and automatic total calculation.
* MPesa STK Push integration.
* Real-time stock updates.
* Receipt generation (PDF/email/print).
* Dashboard with charts and KPIs.
* Sales and inventory reporting.
* Search products by name or barcode.
* Self-service and cashier-assisted checkout modes.

## 🗄 Database Schema (Simplified)

```
Product
- id
- name
- description
- barcode
- price
- stock
- created_at

Order
- id
- customer_id (FK)
- total_price
- status (Pending, Paid, Failed)
- created_at, updated_at

OrderItem
- id
- order_id (FK)
- product_id (FK)
- quantity
- subtotal

Payment
- id
- order_id (FK)
- mpesa_receipt_no
- amount
- status (Success, Failed, Cancelled)
- transaction_date

Customer
- id
- name
- phone_number
- email
- created_at
```

## ⚡ Example Dashboard Layout

* KPIs: Total Sales Today, Total Revenue This Week, Remaining Stock Value
* Charts:

  * Bar: Top 5 Products Sold
  * Line: Sales Trend Over Time
  * Pie: Payment Status Breakdown
* Tables:

  * Orders Table (search, filter, export)
  * Stock Table (barcode/name lookup)

## 🚀 Technology Stack

* Backend: Django 5.2, Django REST Framework
* Payments: Safaricom MPesa Daraja API (STK Push)
* Database: SQLite (development), PostgreSQL/MySQL (production)
* Frontend: Django Templates (can extend with React/Vue)
* Reports: Pandas, OpenPyXL (Excel), WeasyPrint/ReportLab (PDF)
* Deployment: Heroku, Render, or VPS with ngrok for dev

## ▶️ Run Locally

```bash
git clone https://github.com/yourusername/supermarket-mpesa.git
cd supermarket
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

For testing with ngrok:

```bash
ngrok http 8000
```

Use the generated ngrok URL as your callback URL in views.py.

## 📊 Future Enhancements

* QR code receipts for faster verification.
* Customer loyalty program.
* Advanced analytics with AI-based predictions.
* Mobile app integration.
* Barcode scanner support for POS.

## 🤝 Contributing

Fork this repo and submit PRs for improvements.

## 📜 License

MIT License – Free to use and modify.

## 💡 Author

THORIUM234

---
