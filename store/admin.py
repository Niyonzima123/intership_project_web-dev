from django.contrib import admin
from .models import Category, Product, Order, OrderItem, ShippingAddress


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'price', 'stock', 'category', 'is_available', 'is_featured', 'created_at')
    list_filter = ('category', 'is_available', 'is_featured', 'brand')
    list_editable = ('price', 'stock', 'is_available', 'is_featured')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description', 'brand')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'date_added')


class ShippingAddressInline(admin.StackedInline):
    model = ShippingAddress
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'user', 'date_ordered', 'complete', 'status', 'get_cart_total', 'transaction_id')
    list_filter = ('complete', 'status')
    search_fields = ('transaction_id', 'user__username', 'customer_name', 'customer_email')
    inlines = [OrderItemInline, ShippingAddressInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'order', 'quantity', 'date_added')


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'order', 'address', 'city', 'zipcode', 'date_added')
