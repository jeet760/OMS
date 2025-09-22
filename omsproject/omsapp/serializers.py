from rest_framework import serializers
from .models import CustomUser, OrderDetails, SchoolUDISE, SubOrder


class SchoolInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolUDISE
        fields = [
            "pre_primary_students", "i_students", "ii_students", "iii_students",
            "iv_students", "v_students", "vi_students", "vii_students",
            "viii_students", "ix_students", "x_students", "xi_students",
            "xii_students", "total_students", "total_students_with_preprimary",
        ]

class OrderDetailSerializer(serializers.ModelSerializer):
    item_cat = serializers.CharField(source="itemID.itemCat", read_only=True)
    item_name = serializers.CharField(source="itemID.itemName", read_only=True)
    item_unit = serializers.CharField(source="itemID.itemUnit", read_only=True)

    class Meta:
        model = OrderDetails
        fields = ["item_cat", "item_name", "itemQty", "item_unit"]


class SubOrderWithDeliverySerializer(serializers.ModelSerializer):
    delivery_date = serializers.DateTimeField(source="orderdelivery.deliveryDate", read_only=True)
    details = OrderDetailSerializer(source="orderdetails", many=True, read_only=True)

    class Meta:
        model = SubOrder
        fields = ["delivery_date", "details"]


class OrderSerializer(serializers.ModelSerializer):
    school_info = SchoolInfoSerializer(source="school", read_only=True)
    order_details = SubOrderWithDeliverySerializer(
        source="customer_orders",  # use related_name
        many=True,
        read_only=True
    )

    class Meta:
        model = CustomUser
        fields = ["id", "userType", "first_name", "school_info", "order_details"]

    def get_order_details(self, obj):
        orders = []
        for suborder in obj.customer_orders.filter(orderStatus='Delivered'):  # use related_name
            orders.append({
                "delivery_date": suborder.orderdelivery.deliveryDate,
                "details": OrderDetailSerializer(suborder.orderdetails.all(), many=True).data
            })
        return OrderDetailSerializer(orders, many=True).data

    def get_school_info(self, obj):
        if obj.school:
            return SchoolInfoSerializer(obj.school).data
        return None
