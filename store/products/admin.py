from django.contrib import admin
from .models import Brand, Category, Product, ProductImage

# Register your models here.
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product) # change the way the product model is displayed in admin panel
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ('name', 'brand', 'price', 'discount', 'final_price', 'stock', 'description')
    list_filter = ('brand', 'category')
    search_fields = ('name','description', 'brand__name', 'category__name')

@admin.register(Brand) # change the way the brand model is displayed in admin panel
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count')
    search_fields = ('name',)


    # displays the number of products in each brand
    def product_count(self, obj):
        return obj.product_set.count()

@admin.register(Category) # change the way the category model is displayed in admin panel
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_count')
    search_fields = ('name',)

    # displays the number of products in each category
    def category_count(self, obj):
        return obj.product_set.count()