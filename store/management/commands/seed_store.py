from django.core.management.base import BaseCommand
from django.utils.text import slugify

from store.models import Category, Product


class Command(BaseCommand):
    help = 'Load sample electronics categories and products'

    def handle(self, *args, **options):
        catalog = {
            'Laptops': {
                'description': 'Work and gaming notebooks',
                'products': [
                    ('Dell XPS 13', 'Dell', 1299.00, 8, True, '13-inch ultrabook with Intel Core Ultra and a bright OLED display.'),
                    ('HP Pavilion 15', 'HP', 749.00, 12, False, 'Everyday 15-inch laptop for students and office work.'),
                    ('Lenovo Legion 5', 'Lenovo', 1499.00, 6, True, 'Gaming laptop with RTX graphics and a 165Hz display.'),
                ],
            },
            'Smartphones': {
                'description': 'Flagship and mid-range phones',
                'products': [
                    ('Samsung Galaxy S24', 'Samsung', 899.00, 20, True, 'Compact Android flagship with a bright AMOLED screen.'),
                    ('iPhone 15', 'Apple', 999.00, 15, True, 'A16 Bionic, USB-C, and a dual-camera system.'),
                    ('Google Pixel 8', 'Google', 699.00, 10, False, 'Clean Android with excellent computational photography.'),
                ],
            },
            'Tablets': {
                'description': 'Portable tablets for work and media',
                'products': [
                    ('iPad Air 11', 'Apple', 599.00, 9, False, 'Lightweight tablet with M-series performance.'),
                    ('Samsung Galaxy Tab S9', 'Samsung', 649.00, 7, False, 'AMOLED Android tablet with S Pen support.'),
                ],
            },
            'Headphones': {
                'description': 'Wireless and studio audio',
                'products': [
                    ('Sony WH-1000XM5', 'Sony', 349.00, 25, True, 'Industry-leading noise cancelling over-ear headphones.'),
                    ('Apple AirPods Pro 2', 'Apple', 249.00, 30, False, 'In-ear ANC earbuds with USB-C charging case.'),
                    ('JBL Tune 760NC', 'JBL', 99.00, 40, False, 'Budget wireless headphones with active noise cancelling.'),
                ],
            },
            'Televisions': {
                'description': '4K and smart TVs',
                'products': [
                    ('LG OLED C4 55"', 'LG', 1299.00, 4, True, '55-inch OLED TV with webOS and excellent contrast.'),
                    ('Samsung Crystal UHD 65"', 'Samsung', 799.00, 5, False, '65-inch 4K smart TV for movies and sports.'),
                ],
            },
            'Accessories': {
                'description': 'Chargers, mice, and storage',
                'products': [
                    ('Anker 737 Power Bank', 'Anker', 129.00, 18, False, '140W portable charger for laptops and phones.'),
                    ('Logitech MX Master 3S', 'Logitech', 99.00, 22, False, 'Ergonomic wireless mouse for productivity.'),
                    ('Samsung T7 1TB SSD', 'Samsung', 109.00, 16, False, 'Portable USB 3.2 SSD for fast backups.'),
                ],
            },
        }

        created_products = 0
        for category_name, payload in catalog.items():
            category, _ = Category.objects.get_or_create(
                slug=slugify(category_name),
                defaults={'name': category_name, 'description': payload['description']},
            )
            for name, brand, price, stock, featured, description in payload['products']:
                _, created = Product.objects.get_or_create(
                    slug=slugify(name),
                    defaults={
                        'category': category,
                        'name': name,
                        'brand': brand,
                        'description': description,
                        'price': price,
                        'stock': stock,
                        'is_available': True,
                        'is_featured': featured,
                    },
                )
                if created:
                    created_products += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seed complete. Categories: {Category.objects.count()}, new products: {created_products}.'
        ))
