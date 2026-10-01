from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Storefront & Search
    path('', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    # Cart & Checkout
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),

    # Product Management CRUD (Staff)
    path('manage/products/', views.product_manage_list, name='product_manage_list'),
    path('manage/products/create/', views.add_product, name='product_create'),
    path('manage/products/<int:product_id>/edit/', views.product_update, name='product_update'),
    path('manage/products/<int:product_id>/delete/', views.product_delete, name='product_delete'),

    # AI Chatbot Assistant API
    path('api/chatbot/', views.ai_chatbot_response, name='ai_chatbot_response'),
]
