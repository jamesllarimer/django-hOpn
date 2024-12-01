import stripe
from django.conf import settings

stripe.api_key = settings.TEST_STRIPE_SECRET_KEY

def get_stripe_price_id(league, is_member):
    """
    Fetch and determine the appropriate Stripe price ID based on membership status 
    """
    try:
        # Fetch all prices for the product
        prices = stripe.Price.list(
            product=league.stripe_product_id,
            active=True
        )
        
        # Find the appropriate price based on metadata
        for price in prices.data:
            metadata = price.metadata
            print(metadata)
            if metadata.get('is_member', '').lower() == str(is_member).lower():
                return price.id
                
        return None
        
    except stripe.error.StripeError as e:
        print(f"Stripe error: {str(e)}")
        return None