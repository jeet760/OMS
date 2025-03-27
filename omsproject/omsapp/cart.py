from django.conf import settings
from decimal import Decimal
from .models import Item

class Cart:
    def __init__(self, request):
        """Initialize the cart."""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False):
        """Add a product to the cart or update its quantity."""
        product_id = str(product.itemID)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.itemPrice)}
        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        """Mark the session as modified to ensure it is saved."""
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def remove(self, product):
        """Remove a product from the cart."""
        product_id = str(product.itemID)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """Iterate over the items in the cart and get the products from the database."""
        product_ids = self.cart.keys()
        # Get the product objects and add them to the cart items
        products = Item.objects.filter(itemID__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart_item = cart[str(product.itemID)]
            cart_item['product'] = product
            cart_item['price'] = Decimal(cart_item['price'])
            cart_item['total_price'] = cart_item['price'] * cart_item['quantity']
            yield cart_item

    def __len__(self):
        """Count all items in the cart."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Calculate the total price of all items."""
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        """Remove cart from session."""
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True
