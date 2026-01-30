from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from products.models import Product

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    phone = models.CharField(max_length=13)
    address = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.status}"
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

"""
fetch("http://127.0.0.1:8000/api/cart/checkout/", {
  method: "POST",
  headers: {
    "Authorization": "Token aaba293da77c18b4d823cc7780d1fe330e965b25",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    phone: "01012345678",
    address: "Nasr City, Cairo"
  })
})
.then(res => res.json())
.then(data => console.log(data))
.catch(err => console.error(err));


Method to test checkout API
"""