# supermarket/product/context_processors.py

def cart_count(request):
    cart = request.session.get("cart", {})
    total_items = 0

    for item in cart.values():
        if isinstance(item, dict):  
            total_items += item.get("quantity", 0)
        elif isinstance(item, int):  
            total_items += item  # treat plain int as quantity
        else:
            total_items += 0  # ignore unexpected cases

    return {"cart_count": total_items}
