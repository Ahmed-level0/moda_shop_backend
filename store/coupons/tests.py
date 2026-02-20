from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from products.models import Product, Category
from cart.models import Cart, CartItem
from coupons.models import Coupon
from decimal import Decimal
import datetime

class CouponModelTest(TestCase):
    def setUp(self):
        self.coupon = Coupon.objects.create(
            code='SAVE10',
            discount=Decimal('10.00'),
            discount_type='percentage',
            valid_from=timezone.now() - datetime.timedelta(days=1),
            valid_until=timezone.now() + datetime.timedelta(days=1),
            usage_limit=5
        )

    def test_coupon_validity(self):
        self.assertTrue(self.coupon.is_valid)
        
        self.coupon.active = False
        self.coupon.save()
        self.assertFalse(self.coupon.is_valid)
        
        self.coupon.active = True
        self.coupon.usage_count = 5
        self.coupon.save()
        self.assertFalse(self.coupon.is_valid)

class CouponApplicationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            price=Decimal('100.00'),
            category=self.category,
            stock=10
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        
        self.coupon_pct = Coupon.objects.create(
            code='PCT10',
            discount=Decimal('10.00'),
            discount_type='percentage',
            valid_from=timezone.now() - datetime.timedelta(days=1),
            valid_until=timezone.now() + datetime.timedelta(days=1)
        )
        self.coupon_fixed = Coupon.objects.create(
            code='FIXED20',
            discount=Decimal('20.00'),
            discount_type='fixed',
            valid_from=timezone.now() - datetime.timedelta(days=1),
            valid_until=timezone.now() + datetime.timedelta(days=1)
        )

    def test_cart_total_with_percentage_coupon(self):
        # Items total: 2 * 100 = 200
        # Discount: 10% of 200 = 20
        # Expected total: 180
        self.cart.coupon = self.coupon_pct
        self.cart.save()
        self.assertEqual(self.cart.total_price, Decimal('180.00'))

    def test_cart_total_with_fixed_coupon(self):
        # Items total: 200
        # Discount: 20
        # Expected total: 180
        self.cart.coupon = self.coupon_fixed
        self.cart.save()
        self.assertEqual(self.cart.total_price, Decimal('180.00'))
