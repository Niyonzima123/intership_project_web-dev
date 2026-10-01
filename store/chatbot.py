from decimal import Decimal, InvalidOperation
import re

from django.db.models import Q

from .models import Category, Product


def _format_product(product):
    stock_label = f"{product.stock} in stock" if product.in_stock else "out of stock"
    brand = f" ({product.brand})" if product.brand else ""
    return f"{product.name}{brand} — ${product.price} | {product.category.name} | {stock_label}"


def generate_chatbot_reply(message):
    """Rule-based store assistant for products, prices, and categories."""
    text = (message or "").strip()
    if not text:
        return "Please type a question about our electronics, prices, or categories."

    lowered = text.lower()
    products = Product.objects.filter(is_available=True).select_related('category')
    categories = Category.objects.all()

    if any(word in lowered for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
        return (
            "Hello! I am ElectroBot, your ElectroTech shopping assistant. "
            "Ask me about product prices, categories, or what we currently sell."
        )

    if any(word in lowered for word in ['help', 'what can you', 'how do']):
        return (
            "You can ask things like:\n"
            "- What categories do you sell?\n"
            "- Show me laptops\n"
            "- What is the price of Galaxy S24?\n"
            "- What is the cheapest headphone?\n"
            "- Do you have tablets in stock?"
        )

    if 'categor' in lowered:
        if not categories.exists():
            return "No product categories have been added yet."
        names = ", ".join(c.name for c in categories)
        return f"We currently sell these categories: {names}."

    if any(word in lowered for word in ['cheapest', 'lowest price', 'budget']):
        cheapest = products.order_by('price').first()
        if not cheapest:
            return "There are no products in the catalog yet."
        return f"The lowest priced item is { _format_product(cheapest) }."

    if any(word in lowered for word in ['expensive', 'highest price', 'premium']):
        priciest = products.order_by('-price').first()
        if not priciest:
            return "There are no products in the catalog yet."
        return f"The highest priced item is { _format_product(priciest) }."

    price_match = re.search(r'(?:under|below|less than|cheaper than)\s*\$?\s*(\d+(?:\.\d+)?)', lowered)
    if price_match:
        try:
            limit = Decimal(price_match.group(1))
        except InvalidOperation:
            limit = None
        if limit is not None:
            matches = list(products.filter(price__lte=limit).order_by('price')[:6])
            if not matches:
                return f"I could not find products priced under ${limit}."
            listing = "\n".join(f"- {_format_product(p)}" for p in matches)
            return f"Products under ${limit}:\n{listing}"

    matched_category = None
    for category in categories:
        if category.name.lower() in lowered or category.slug.replace('-', ' ') in lowered:
            matched_category = category
            break

    if matched_category:
        category_products = list(products.filter(category=matched_category)[:8])
        if not category_products:
            return f"The {matched_category.name} category is empty right now."
        listing = "\n".join(f"- {_format_product(p)}" for p in category_products)
        return f"{matched_category.name} products:\n{listing}"

    keywords = [token for token in re.findall(r'[a-z0-9]+', lowered) if len(token) > 2]
    stopwords = {
        'the', 'and', 'for', 'you', 'have', 'what', 'price', 'cost', 'how', 'much',
        'show', 'list', 'find', 'product', 'products', 'please', 'tell', 'about',
        'your', 'this', 'that', 'with', 'from', 'stock',
    }
    keywords = [word for word in keywords if word not in stopwords]

    if keywords:
        query = Q()
        for word in keywords:
            query |= Q(name__icontains=word) | Q(description__icontains=word) | Q(brand__icontains=word)
        matches = list(products.filter(query).distinct()[:8])
        if matches:
            if any(word in lowered for word in ['price', 'cost', 'how much']) and len(matches) == 1:
                product = matches[0]
                return f"{product.name} costs ${product.price}. Category: {product.category.name}. {product.stock} units available."
            listing = "\n".join(f"- {_format_product(p)}" for p in matches)
            return f"Here is what I found:\n{listing}"

    if any(word in lowered for word in ['product', 'sell', 'catalog', 'available', 'stock']):
        sample = list(products[:8])
        if not sample:
            return "The store catalog is empty at the moment."
        listing = "\n".join(f"- {_format_product(p)}" for p in sample)
        return f"Here are some products we currently sell:\n{listing}"

    return (
        "I could not find a matching product. Try a product name, a category "
        "(laptops, smartphones, headphones), or ask for prices."
    )
