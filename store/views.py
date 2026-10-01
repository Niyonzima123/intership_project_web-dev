import json
import uuid

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .chatbot import generate_chatbot_reply
from .forms import CheckoutForm, ProductForm
from .models import Category, Order, OrderItem, Product


def _build_cart_items(cart):
    cart_items = []
    grand_total = 0
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            quantity = int(quantity)
            total_price = product.price * quantity
            grand_total += total_price
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_price': total_price,
            })
        except (Product.DoesNotExist, TypeError, ValueError):
            continue
    return cart_items, grand_total


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(is_available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__name__icontains=query)
        )

    sort_by = request.GET.get('sort')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('-is_featured', '-created_at')

    featured_products = Product.objects.filter(is_available=True, is_featured=True)[:4]

    context = {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query,
        'sort_by': sort_by,
        'featured_products': featured_products,
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    related_products = Product.objects.filter(
        category=product.category,
        is_available=True,
    ).exclude(id=product.id)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })


def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items, grand_total = _build_cart_items(cart)
    context = {
        'cart_items': cart_items,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart_detail.html', context)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    cart = request.session.get('cart', {})
    str_id = str(product_id)

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            quantity = 1
    else:
        quantity = 1

    if quantity < 1:
        quantity = 1

    current_qty = int(cart.get(str_id, 0))
    new_qty = current_qty + quantity
    if new_qty > product.stock:
        messages.error(request, f"Only {product.stock} unit(s) of {product.name} are available.")
        return redirect('store:product_detail', slug=product.slug)

    cart[str_id] = new_qty
    request.session['cart'] = cart
    messages.success(request, f"Added {product.name} to your cart.")
    return redirect('store:cart_detail')


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    str_id = str(product_id)

    if str_id in cart:
        del cart[str_id]
        request.session['cart'] = cart
        messages.info(request, "Item removed from cart.")

    return redirect('store:cart_detail')


@require_POST
def update_cart(request, product_id):
    cart = request.session.get('cart', {})
    str_id = str(product_id)
    product = get_object_or_404(Product, id=product_id)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity <= 0:
        cart.pop(str_id, None)
        messages.info(request, f"{product.name} removed from cart.")
    elif quantity > product.stock:
        messages.error(request, f"Only {product.stock} unit(s) of {product.name} are available.")
    else:
        cart[str_id] = quantity
        messages.success(request, "Cart updated.")

    request.session['cart'] = cart
    return redirect('store:cart_detail')


def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('store:product_list')

    cart_items, grand_total = _build_cart_items(cart)
    if not cart_items:
        messages.warning(request, "Your cart no longer contains valid products.")
        request.session['cart'] = {}
        return redirect('store:product_list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    for item in cart_items:
                        product = Product.objects.select_for_update().get(pk=item['product'].pk)
                        if product.stock < item['quantity']:
                            raise ValueError(f"Not enough stock for {product.name}.")

                    order = Order.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        status='Pending',
                        transaction_id=str(uuid.uuid4()),
                        customer_name=form.cleaned_data['full_name'],
                        customer_email=form.cleaned_data['email'],
                    )

                    shipping_address = form.save(commit=False)
                    shipping_address.order = order
                    if request.user.is_authenticated:
                        shipping_address.user = request.user
                    shipping_address.save()

                    for item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=item['product'],
                            quantity=item['quantity'],
                        )
                        Product.objects.filter(pk=item['product'].pk).update(
                            stock=F('stock') - item['quantity']
                        )

                    order.complete = True
                    order.status = 'Processing'
                    order.save()
            except ValueError as exc:
                messages.error(request, str(exc))
                return redirect('store:cart_detail')

            request.session['cart'] = {}
            request.session['last_order_id'] = order.id
            messages.success(request, f"Order placed successfully! Order ID: #{order.id}")
            return redirect('store:order_success', order_id=order.id)
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data['full_name'] = (
                f"{request.user.first_name} {request.user.last_name}".strip()
                or request.user.username
            )
            initial_data['email'] = request.user.email
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart_items': cart_items,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, complete=True)
    if not request.user.is_staff:
        last_order_id = request.session.get('last_order_id')
        if last_order_id != order.id:
            messages.error(request, "You cannot view that order.")
            return redirect('store:product_list')
    return render(request, 'store/order_success.html', {'order': order})


def ai_chatbot_response(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        payload = {}

    message = payload.get('message') or request.POST.get('message', '')
    reply = generate_chatbot_reply(message)
    return JsonResponse({'reply': reply})


@staff_member_required
def product_manage_list(request):
    products = Product.objects.select_related('category').all()
    query = request.GET.get('q')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(brand__icontains=query))
    return render(request, 'store/manage_products.html', {
        'products': products,
        'query': query,
    })


@staff_member_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product.name}' created successfully.")
            return redirect('store:product_manage_list')
    else:
        form = ProductForm()
    return render(request, 'store/product_form.html', {
        'form': form,
        'title': 'Add Product',
    })


@staff_member_required
def product_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect('store:product_manage_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/product_form.html', {
        'form': form,
        'product': product,
        'title': 'Edit Product',
    })


@staff_member_required
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.info(request, f"Product '{name}' deleted.")
        return redirect('store:product_manage_list')
    return render(request, 'store/product_confirm_delete.html', {'product': product})
