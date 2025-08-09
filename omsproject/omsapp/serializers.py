# omsapp/serializers.py
from rest_framework import serializers
from .models import OrderDetails

class OrderSerializer(serializers.ModelSerializer):
    item_name= serializers.CharField(source='itemID.itemName', read_only=True)
    item_cat = serializers.CharField(source='itemID.itemCat', read_only=True)
    class Meta:
        model = OrderDetails
        fields = ['item_name', 'item_cat', 'itemQty']
