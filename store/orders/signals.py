from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail

from .models import Order
from django.conf import settings


@receiver(pre_save, sender=Order)
def order_status_changed(sender, instance, **kwargs):

    # New order (no ID yet)
    if not instance.pk:
        return

    try:
        old_order = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    old_status = old_order.status
    new_status = instance.status

    # If status did not change → do nothing
    if old_status == new_status:
        return

    user_email = instance.user.email

    if not user_email:
        return
    
    if new_status == 'pending':  
        subject = f"Order #{instance.id} Update"
        message = f"""
    Hello {instance.user.username},

    Your order #{instance.id} has been place and waiting for payment.
    Total: {instance.total_price} EGP

    Thank you for shopping with us.
    Moda House.
    """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
    
    if new_status == 'cancelled':  
        subject = f"Order #{instance.id} Update"
        message = f"""
    Hello {instance.user.username},

    Your order #{instance.id} has been cancelled under the demand of your's.

    Thank you for shopping with us.
    
    Moda House.
    """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
    
    if new_status == 'paid':  
        subject = f"Order #{instance.id} Update"
        message = f"""
    Hello {instance.user.username},

    Thank you for Payment for order #{instance.id}.
    Total: {instance.total_price} EGP
    You will get an email once the order is shipped for you. 
    Thank you for shopping with us.
    Moda House.
    """
    
    if new_status == 'shipped':  
        subject = f"Order #{instance.id} Update"
        message = f"""
    Hello {instance.user.username},

    Your Order #{instance.id} Has been shipped and it's on his way to you.
    for any problems please contact us at +20123456789.

    Thank you for shopping with us.
    Moda House.
    """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
    
    if new_status == 'delivered':  
        subject = f"Order #{instance.id} Update"
        message = f"""
    Hello {instance.user.username},

    Your Order #{instance.id} Has been Delivered safely.

    for any problems please contact us at +20123456789.
    we look forward to seeing you again!

    Thank you for shopping with us.
    Moda House.
    """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
