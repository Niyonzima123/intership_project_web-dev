import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from store.models import Category, Order, Product


class StoreTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Laptops',
            slug='laptops',
            description='Notebooks',
        )
        self.product = Product.objects.create(
            category=self.category,
            name='Test Laptop',
            slug='test-laptop',
            brand='TestBrand',
            description='A reliable test laptop',
            price='999.00',
            stock=5,
            is_available=True,
            is_featured=True,
        )
        self.staff = User.objects.create_user(
            username='staff',
            password='staffpass123',
            is_staff=True,
        )

    def test_catalog_renders_product(self):
        response = self.client.get(reverse('store:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Laptop')
        self.assertContains(response, 'ElectroBot')

    def test_category_filter_and_search(self):
        response = self.client.get(reverse('store:product_list_by_category', args=['laptops']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Laptop')

        response = self.client.get(reverse('store:product_list'), {'q': 'Test Laptop'})
        self.assertContains(response, 'Test Laptop')

        response = self.client.get(reverse('store:product_list'), {'q': 'missing-device'})
        self.assertContains(response, 'No products found')

    def test_product_detail(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '999.00')

    def test_add_update_remove_cart(self):
        add_url = reverse('store:add_to_cart', args=[self.product.id])
        response = self.client.post(add_url, {'quantity': 2}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Laptop')
        self.assertEqual(self.client.session['cart'][str(self.product.id)], 2)

        update_url = reverse('store:update_cart', args=[self.product.id])
        self.client.post(update_url, {'quantity': 3})
        self.assertEqual(self.client.session['cart'][str(self.product.id)], 3)

        remove_url = reverse('store:remove_from_cart', args=[self.product.id])
        self.client.get(remove_url)
        self.assertNotIn(str(self.product.id), self.client.session.get('cart', {}))

    def test_checkout_creates_order_and_reduces_stock(self):
        self.client.post(reverse('store:add_to_cart', args=[self.product.id]), {'quantity': 2})
        response = self.client.post(reverse('store:checkout'), {
            'full_name': 'Jane Customer',
            'email': 'jane@example.com',
            'phone': '0700000000',
            'address': '12 Market Street',
            'city': 'Nairobi',
            'state': 'Nairobi',
            'zipcode': '00100',
        })
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertTrue(order.complete)
        self.assertEqual(order.get_cart_items, 2)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        success = self.client.get(reverse('store:order_success', args=[order.id]))
        self.assertEqual(success.status_code, 200)

    def test_chatbot_answers_category_and_price(self):
        url = reverse('store:ai_chatbot_response')
        response = self.client.post(
            url,
            data=json.dumps({'message': 'What categories do you sell?'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Laptops', response.json()['reply'])

        response = self.client.post(
            url,
            data=json.dumps({'message': 'price of Test Laptop'}),
            content_type='application/json',
        )
        self.assertIn('999', response.json()['reply'])

    def test_staff_product_crud_requires_login(self):
        manage_url = reverse('store:product_manage_list')
        response = self.client.get(manage_url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username='staff', password='staffpass123')
        response = self.client.get(manage_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Laptop')
