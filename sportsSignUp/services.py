import stripe
from django.conf import settings
from .models import StripeProduct, StripePrice

stripe.api_key = settings.TEST_STRIPE_SECRET_KEY

def sync_stripe_products():
    """
    Sync all Stripe products and their prices to Django models.
    Returns a tuple of (products_synced, prices_synced)
    """
    products_synced = 0
    prices_synced = 0
    
    # Fetch all active products from Stripe
    stripe_products = stripe.Product.list(active=True)
    
    for stripe_product in stripe_products:
        # Create or update product
        product, created = StripeProduct.objects.update_or_create(
            stripe_id=stripe_product.id,
            defaults={
                'name': stripe_product.name,
                'description': stripe_product.description or '',
                'active': stripe_product.active,
                'metadata': stripe_product.metadata,
            }
        )
        if created:
            products_synced += 1
        
        # Fetch all prices for this product
        stripe_prices = stripe.Price.list(product=stripe_product.id, active=True)
        
        for stripe_price in stripe_prices:
            price_data = {
                'product': product,
                'currency': stripe_price.currency,
                'unit_amount': stripe_price.unit_amount,
                'active': stripe_price.active,
                'metadata': stripe_price.metadata,
                'description': stripe_price.nickname or '',
            }
            
            if stripe_price.recurring:
                price_data.update({
                    'recurring': True,
                    'recurring_interval': stripe_price.recurring.interval,
                    'recurring_interval_count': stripe_price.recurring.interval_count,
                })
            
            _, created = StripePrice.objects.update_or_create(
                stripe_id=stripe_price.id,
                defaults=price_data
            )
            if created:
                prices_synced += 1
    
    return products_synced, prices_synced
