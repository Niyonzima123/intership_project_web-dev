from .models import Category


def cart_context(request):
    cart = request.session.get('cart', {})
    count = 0
    for quantity in cart.values():
        try:
            count += int(quantity)
        except (TypeError, ValueError):
            continue
    return {
        'cart_item_count': count,
        'nav_categories': Category.objects.all(),
    }
