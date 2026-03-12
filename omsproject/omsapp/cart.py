from django.conf import settings
from decimal import Decimal
from .models import Item, ItemPincodeMap

class Cart:
    def __init__(self, request):
        """Initialize the cart."""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        pincode = request.session.get('pincode')
        if pincode is None:
            pincode = '000000'  # Default pincode if not set in session
        if not cart:
            # Save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.pincode = pincode

    def add(self, product, quantity=1, update_quantity=False):
        """Add a product to the cart or update its quantity."""
        product_id = str(product.itemID)
        if self.pincode == '000000':
            item_selling_price = ItemPincodeMap.objects.filter(
                itemID=product.itemID).first()
        else:
            item_selling_price = ItemPincodeMap.objects.get(
                itemID=product.itemID,
                pinCode1__pinCode1=self.pincode)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(item_selling_price.selling_price)}
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
        #get the pincode
        pincode = self.pincode if self.pincode else '000000'
        # Get the product objects and add them to the cart items
        products = Item.objects.filter(itemID__in=product_ids)
        #Fetch the mapped items based on pincode
        if pincode != '000000':
            mappings = ItemPincodeMap.objects.filter(
                itemID__in=products,
                pinCode1__pinCode1=pincode
            )
        else:
            mappings = ItemPincodeMap.objects.filter(
                itemID__in=products,
                in_stock = True
            )
        # Map: item_id → mapping
        map_dict = {
            m.itemID_id: m for m in mappings
        }
        
        cart = self.cart.copy()
        for product in products:
            cart_item = cart[str(product.itemID)]
            mapping = map_dict.get(product.itemID)
            cart_item['product'] = product
            cart_item['in_stock'] = mapping.in_stock if mapping else False
            cart_item['price'] = Decimal(mapping.selling_price) if mapping else Decimal(0.00)
            cart_item['total_price'] = cart_item['price'] * cart_item['quantity']
            yield cart_item

    def __len__(self):
        """Count all items in the cart."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Calculate the total price of all items."""
        if any("product" not in item for item in self.cart.values()):
            return Decimal("0.00")

        return sum(
            Decimal(item["price"]) * item["quantity"]
            for item in self.cart.values()
            if item.get("in_stock")
        )


    def clear(self):
        """Remove cart from session."""
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True
