from django.db import models
from django.contrib.auth.models import User
from products.models import Product

# Create your models here.
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True) # Indicates if the cart is active or has been checked out

    @property
    def total_price(self):
        total = sum(item.total_price for item in self.items.all())
        return total
    
    def __str__(self):
        return f"Cart {self.id} - {self.user.username}"
    
    class Meta:
        # Ensure a user can have only one active cart at a time
        constraints = [
            models.UniqueConstraint(
                fields=['user'], # user field is unique when the cart is active
                condition=models.Q(is_active=True), # only one active cart per user
                name='unique_active_cart_per_user'# constraint name
            )
        ]
    
# the items in the cart
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Prevent adding items to an inactive cart by raising an error
        if not self.cart.is_active:
            raise ValueError("Cannot add items to an inactive cart")
        super().save(*args, **kwargs)

    @property
    def total_price(self):
        return self.product.final_price * self.quantity