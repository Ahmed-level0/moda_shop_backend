from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length= 20)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length= 20)

    def __str__(self):
        return self.name
     
class Product(models.Model):
    name  = models.CharField(max_length= 25)
    category = models.ForeignKey(Category, on_delete=models.CASCADE) # Each product belongs to one category when deleted, delete all products in that category
    price = models.DecimalField(max_digits= 8, decimal_places= 2)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, default= None) # Each product belongs to one brand when deleted, delete all products in that brand
    discount = models.PositiveIntegerField(default= 0) # Allows only positive values
    stock = models.PositiveIntegerField(default= 0)
    description = models.TextField(blank= True)

    # Calculate the final price after applying discount
    @property
    def final_price(self):
        discount_validation = min(self.discount, 100) # Ensure discount does not exceed 100%
        return self.price * (100 - discount_validation) / 100

    # Check if the product is in stock
    @property
    def in_stock(self):
        return self.stock > 0
    
    def save (self, *args, **kwargs):
        # Ensure stock is not 0 before saving
        if self.stock == 0:
            raise ValueError("Can't add 0 stock for a product")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE, # when a product is deleted, delete all associated images
        related_name='images' # allows accessing images of a product using product.images.all()
    )
    image = models.ImageField(upload_to='products/') # Store images in 'products/' directory