from rest_framework import serializers
from .models import CustomUser, OrderDetails, SchoolUDISE


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


class OrderSerializer(serializers.ModelSerializer):
    school_info = serializers.SerializerMethodField()
    order_details = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ["id", "userType", "last_name", "udise_code", "school_info", "order_details"]

    def get_school_info(self, obj):
        school_map = self.context.get("school_map", {})
        schools = school_map.get(obj.udise_code, [])
        if not schools:
            return None
        # return the first match OR all matches
        return SchoolInfoSerializer(schools, many=True).data

    def get_order_details(self, obj):
        orders_map = self.context.get("orders_map", {})
        orders = orders_map.get(obj.id, [])
        return OrderDetailSerializer(orders, many=True).data
