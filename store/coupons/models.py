from django.db import models

# Create your models here.
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )

    code = models.CharField(max_length=15, unique=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Empty for unlimited usage")
    usage_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.code} ({self.discount_type})"

    @property
    def is_valid(self):
        now = timezone.now()
        if not self.active:
            return False
        if self.valid_from > now or self.valid_until < now:
            return False
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        return True

    
