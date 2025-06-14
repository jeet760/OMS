from django.contrib import admin
from .models import Cart, CartItem, CustomUser, Item, ItemStock, Login, Order, OrderDetails, OrderDelivery, OrderInvoice

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Login)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Item)
admin.site.register(ItemStock)
admin.site.register(Order)
admin.site.register(OrderDetails)
admin.site.register(OrderInvoice)
admin.site.register(OrderDelivery)



