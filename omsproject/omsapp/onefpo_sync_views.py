import json
import requests
from django.conf import settings    
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Item, ItemPincodeMap, CustomUser, FPOServingAddresses,\
    Order, SubOrder, OrderDetails, UserBillingAddresses, UserShippingAddresses,\
    OrderInvoice, OrderDelivery,\
    BulkBuy, BulkBuyDetails, BulkBuyResponse, BulkBuyResponseDetails


SYNC_TOKEN = settings.ONEFPO_SYNC_TOKEN
ONEFPO_SYNC_ORDER_URL = settings.ONEFPO_SYNC_ORDER_URL
TOKEN = settings.ONEFPO_SYNC_TOKEN

@csrf_exempt
def sync_item(request):
    """
    Synchronizes item data from OneFPO.
    Expects a POST request with JSON body containing an "items" list.
    """
    # -------------------- Auth --------------------

    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    token = request.headers.get("Authorization")

    if token != f"Bearer {SYNC_TOKEN}":
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # -------------------- Load JSON --------------------

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    blocks = data.get("items", [])

    if not blocks:
        return JsonResponse({"error": "No items"}, status=400)

    # -------------------- Cache Users --------------------

    usernames = {
        b["item"]["username"]
        for b in blocks
        if "username" in b["item"]
    }

    users = {
        u.username: u
        for u in CustomUser.objects.filter(
            username__in=usernames
        )
    }

    results = []

    # -------------------- Atomic Sync --------------------

    try:
        with transaction.atomic():

            for block in blocks:

                item_data = block["item"]
                pin_data = block["pincodes"]

                username = item_data["username"]

                user = users.get(username)

                if not user:
                    continue

                # -------------------- Item Upsert --------------------

                item, created = Item.objects.update_or_create(

                    onefpo_itemID=item_data["id"],

                    defaults={

                        "itemName": item_data["name"],
                        "itemType": item_data["type"],
                        "itemCat": item_data["category"],

                        "itemSku": item_data["sku"],
                        "itemHSNCode": item_data["hsn"],
                        "itemUnit": item_data["unit"],

                        "itemDesc": item_data["desc"],

                        "itemTaxPref": item_data["tax_pref"],
                        "itemTaxRate": item_data["tax_rate"],

                        "itemCostPrice": item_data["purchase_price"],
                        "itemPrice": item_data["sale_price"],

                        "itemImg": item_data["image_url"],

                        "itemActive": True,
                        "itemInStock": True,
                        "featureItem": True,

                        "stockValue": len(
                            [p for p in pin_data if p["in_stock"]]
                        ),

                        "userID": user,
                    }
                )

                # -------------------- Pincode Mapping --------------------

                for p in pin_data:

                    area, _ = FPOServingAddresses.objects.get_or_create(
                        pinCode1=p["pincode"], userID=user
                    )

                    ItemPincodeMap.objects.update_or_create(

                        itemID=item,
                        pinCode1=area,

                        defaults={

                            "cost_price": p["cost_price"],
                            "selling_price": p["sale_price"],

                            "is_active": p["is_active"],
                            "in_stock": p["in_stock"],
                            "in_feature": p["in_feature"],

                            "on_discount": p["on_discount"],
                            "discount_percentage": p["discount_percentage"],
                            "discount_amount": p["discount_amount"],
                        }
                    )

                results.append({
                    "onefpo_id": item_data["id"],
                    "fh_id": item.itemID,
                    "created": created
                })

    except Exception as e:
        print(str(e))
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

    # -------------------- Response --------------------

    return JsonResponse({
        "status": "ok",
        "count": len(results),
        "results": results
    })

def push_orders_to_onefpo(request,order_id=None):
    """
    Pushes new orders to OneFPO.
     - Fetches all orders with status "Pending Order".
     - For each order, constructs a payload with order and suborder details.
     - Sends the payload to OneFPO via a POST request.
     - Returns the response status from OneFPO.
    """
    orders = (
        Order.objects
        .prefetch_related(
            "suborders__orderdetails",
            "orderdetails"
        )
        .filter(orderStatus="Pending Order", pk=order_id)
    )

    payload = []

    for order in orders:

        order_block = {
            "order": {
                "order_id": order.orderID,
                "order_no": order.orderNo,
                "order_date": str(order.orderDate),
                "order_status": order.orderStatus,
                "order_amount": str(order.orderAmount),
                "order_GST_amount": str(order.orderGSTAmount),
                "order_deduction": str(order.orderDeduction),
                "order_transportation": str(order.orderTransportation),
                "order_grand_total": str(order.orderGrandTotal),
                "sch_delivery_date": order.schDeliveryDate,
                "sch_delivery_time": order.schDeliveryTime,
                "remark": order.remark,
                "username": order.userID.username,
                "payment_mode": order.paymentMode,
                "payment_status": order.paymentStatus,
            },
            "suborders": []
        }

        for sub in order.suborders.all():

            sub_block = {
                "suborder_id": sub.suborderID,
                "suborder_no":sub.suborder_no,
                "vendor_username": sub.vendorID.username,
                "order_status": sub.orderStatus,
                "suborder_amount": str(sub.suborder_amount),
                "suborder_gst_amount":str(sub.suborder_gst_amount),
                "suborder_discount":str(sub.suborder_discount),
                "suborder_total_amount":str(sub.suborder_total_amount),
                "items": []
            }

            for item in sub.orderdetails.all():
                sub_block["items"].append({
                    "onefpo_item_id": item.itemID.onefpo_itemID,
                    "qty": item.itemQty,
                    "price": str(item.itemPrice),
                    "gst": str(item.itemGST),
                    "gst_amount": str(item.itemGSTAmount),
                    "price_with_gst": str(item.itemPricewithGST),
                    "delivery_date": item.deliveryDate,
                    "delivery_time": item.deliveryTime
                })

            order_block["suborders"].append(sub_block)

        payload.append(order_block)

    response = requests.post(
        settings.ONEFPO_SYNC_ORDER_URL,
        json={"orders": payload},
        headers={"Authorization": f"Bearer {settings.ONEFPO_SYNC_TOKEN}"}
    )

    return JsonResponse({
        "status": "success",
        "onefpo_status_code": response.status_code
    })

def push_bulk_requests_to_onefpo(request,bulkBuyNo):
    """
    Helper function to push bulk data to OneFPO.
     - Accepts a payload and an endpoint URL.
     - Sends the payload to OneFPO via a POST request.
     - Returns the response status from OneFPO.
    """
    BASE_URL = settings.ONEFPO_SYNC_BASE_URL
    SYNC_URL = settings.ONEFPO_PUSH_BULK_ORDER_URL
    SYNC_TOKEN = settings.ONEFPO_SYNC_TOKEN

    bulk_request = get_object_or_404(BulkBuy, bulkBuyNo=bulkBuyNo)
    bulk_request_details_qs = BulkBuyDetails.objects.filter(bulkBuyID=bulk_request)
    bulk_request_details_list = list(bulk_request_details_qs.values(
        "itemName",
        "itemSpec",
        "itemPrice",
        "itemQty",
        "itemUnit"
    ))
    payload = {
        "order_no": bulk_request.bulkBuyNo,
        "request_date": bulk_request.bulkBuyDate.isoformat(),
        "exp_date": bulk_request.bulkBuyExpDate.isoformat(),
        "username": bulk_request.userID.username,
        "customer_name":bulk_request.userID.last_name,
        "status": bulk_request.response_accept,
        "order_frequency": bulk_request.order_frequency,
        "requested_items": bulk_request_details_list
    }
    headers = {
        "Authorization": f"Bearer {SYNC_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            url = SYNC_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return JsonResponse({
            "status": "success",
            "onefpo_status_code": response.status_code
        })
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def sync_order_status_from_onefpo(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    token = request.headers.get("Authorization")
    if token != f"Bearer {settings.ONEFPO_SYNC_TOKEN}":
        return JsonResponse({"error": "Unauthorized"}, status=401)

    data = json.loads(request.body)

    order_no = data.get("order_no")
    suborder_no = data.get("suborder_no")
    vendor_username = data.get("vendor_username")
    customer_username = data.get("customer_username")
    order_status = data.get("order_status")
    order_remark = data.get("order_remark")
    suborder_status = data.get("suborder_status")
    suborder_remark = data.get("suborder_remark")
    timestamp = data.get("timestamp")
    order_details = data.get("order_details")

    try:
        order = Order.objects.get(
            orderNo = order_no
        )
        suborder = SubOrder.objects.get(
            suborder_no = suborder_no
        )
        order.orderStatus = order_status
        order.remark = order_remark
        order.save()
        suborder.orderStatus = suborder_status
        suborder.remark = suborder_remark
        suborder.save()

        for order_detail in order_details:
            item = Item.objects.get(onefpo_itemID=order_detail["item__gst_item_id"])
            order_item = OrderDetails.objects.get(
                orderID=order,
                suborderID=suborder,
                itemID=item
            )
            order_item.orderStatus = order_detail["order_status"]
            order_item.remark = order_detail["remark"].strip()
            order_item.deliveryDate = order_detail["delivery_date"]
            order_item.deliveryTime = order_detail["delivery_time"]
            order_item.save()

        return JsonResponse({"success": True})

    except Exception as e:
        print(str(e))
        return JsonResponse({"error": str(e)}, status=400)

def sync_customers_to_onefpo(request, username=None):
    """
    Synchronizes customer data to OneFPO.
     - Fetches all unique customers from orders.
     - Constructs a payload with customer details.
     - Sends the payload to OneFPO via a POST request.
     - Returns the response status from OneFPO.
    """
    token = request.headers.get("Authorization")

    if token != f"Bearer {SYNC_TOKEN}":
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        user = CustomUser.objects.get(
            username=username,
            isActive=True
        )
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "Customer not found"}, status=404)

    # Shipping Addresses
    shipping_addresses = []
    for addr in UserShippingAddresses.objects.filter(userID=user, setDefault=True):
        shipping_addresses.append({
            "id": addr.id,
            "address": addr.userAddress1,
            "city": addr.userCity1,
            "city_name": addr.userCity1_name,
            "state": addr.userState1,
            "state_name": addr.userState1_name,
            "district": addr.userDistrict1,
            "district_name": addr.userDistrict1_name,
            "pincode": addr.pinCode1,
            "contact_person": addr.contactPerson1,
            "contact_no": addr.contactNo1,
            "lat": addr.address_lat1,
            "long": addr.address_long1,
            "default": addr.setDefault,
        })

    # Billing Addresses
    billing_addresses = []
    for addr in UserBillingAddresses.objects.filter(userID=user, setDefault=True):
        billing_addresses.append({
            "id": addr.id,
            "address": addr.userAddress,
            "city": addr.userCity,
            "city_name": addr.userCity_name,
            "state": addr.userState,
            "state_name": addr.userState_name,
            "district": addr.userDistrict,
            "district_name": addr.userDistrict_name,
            "pincode": addr.pinCode,
            "contact_person": addr.contactPerson,
            "contact_no": addr.contactNo,
            "lat": addr.address_lat,
            "long": addr.address_long,
            "default": addr.setDefault,
        })

    #user type mapping
    user_type_mapping = {
        '1': 'FPO',
        '2': 'Business',
        '3': 'School',
        '4': 'Overseas',
        '5': 'Individual',
    }
    sync_user_type = user_type_mapping.get(user.userType, 'Unknown')
    
    #gst type mapping
    gst_tmt_mapping = {
        '1': 'Registered Regular',
        '2': 'Registered Composition',
        '3': 'Unregistered',
        '4': 'Consumer',
        '5': 'SEZ',
        '6': 'Deemed Export',
    }
    sync_gst_tmt = gst_tmt_mapping.get(user.gst_tmt, 'Unknown')

    #state mapping
    state_mapping = {
        '28':'Andhra Pradesh',
        '12':'Arunachal Pradesh',
        '18':'Assam',
        '10':'Bihar',
        '22':'Chhattisgarh',
        '30':'Goa',
        '24':'Gujarat',
        '6':'Haryana',
        '2':'Himachal Pradesh',
        '20':'Jharkhand',
        '29':'Karnataka',
        '32':'Kerala',
        '23':'Madhya Pradesh',
        '27':'Maharashtra',
        '14':'Manipur',
        '17':'Meghalaya',
        '15':'Mizoram',
        '13':'Nagaland',
        '21':'Odisha',
        '3':'Punjab',
        '8':'Rajasthan',
        '11':'Sikkim',
        '33':'Tamil Nadu',
        '36':'Telangana',
        '16':'Tripura',
        '9':'Uttar Pradesh',
        '5':'Uttarakhand',
        '19':'West Bengal',
        '35':'Andaman And Nicobar Islands [UT]',
        '4':'Chandigarh [UT]',
        '7':'Delhi [UT]',
        '1':'Jammu And Kashmir [UT]',
        '37':'Ladakh [UT]',
        '31':'Lakshadweep [UT]',
        '34':'Puducherry [UT]',
        '38':'The Dadra And Nagar Haveli And Daman And Diu [UT]'
    }
    sync_user_state = state_mapping.get(user.userState, 'Unknown')

    data = {
        "fh_user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "user_type": sync_user_type,
        "org_name": user.org_name,
        "email": user.email,
        "phone": user.phone,
        "gst_tmt": sync_gst_tmt,
        "gstin": user.gstin,
        "supply_place": sync_user_state,
        "shipping_addresses": shipping_addresses,
        "billing_addresses": billing_addresses,
    }

    return JsonResponse(data)

@csrf_exempt
def sync_invoices_from_onefpo(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    token = request.headers.get("Authorization")
    if token != f"Bearer {SYNC_TOKEN}":
        return JsonResponse({"error": "Unauthorized"}, status=401)

    data = json.loads(request.body)

    order = Order.objects.get(orderNo=data["order_no"])
    suborder = SubOrder.objects.get(suborder_no=data["suborder_no"])

    for invoice in data['invoices']:
        OrderInvoice.objects.create(
            orderID=order,
            suborderID=suborder,
            invoiceNo=invoice["invoice_no"],
            invoiceDate=invoice["invoice_date"],
            invoiceFile=invoice["invoice_url"],
            customer_userID=suborder.customerID
        )

    for invoiced_item in data["invoiced_items"]:
        item = Item.objects.get(onefpo_itemID=invoiced_item["item__gst_item_id"])
        order_item = OrderDetails.objects.get(
            orderID=order,
            suborderID=suborder,
            itemID=item
        )
        order_item.orderStatus = invoiced_item["order_status"]
        order_item.remark = invoiced_item["remark"].strip()
        order_item.save()
    
    suborder.orderStatus = data["suborder_status"]
    suborder.save()
    order.orderStatus = data["order_status"]
    order.save()

    return JsonResponse({"status": "success"})

@csrf_exempt
def sync_delivery_from_onefpo(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status = 405)
    token = request.headers.get("Authorization")
    if token != f"Bearer {SYNC_TOKEN}":
        return JsonResponse({"error":"Unauthrized"}, status = 401)
    
    data = json.loads(request.body)

    try:    
        order = Order.objects.get(orderNo = data["order_no"])
        suborder = SubOrder.objects.get(suborder_no = data["suborder_no"])

        for delivery in data["deliveries"]:
            OrderDelivery.objects.create(
                orderID = order,
                suborderID = suborder,
                deliveryDate=delivery["delivery_date"],
                deliveryImg=delivery["delivery_img"],
                latitude=delivery["latitude"],
                longitude=delivery["longitude"],
                timestamp=delivery["timestamp"]
            )
        
        for delivered_item in data["delivered_items"]:
            item = Item.objects.get(onefpo_itemID=delivered_item["item__gst_item_id"])
            order_item = OrderDetails.objects.get(
                orderID=order,
                suborderID=suborder,
                itemID=item
            )
            order_item.remark = delivered_item["remark"].strip()
            order_item.save()

        suborder.orderStatus = data["suborder_status"]
        suborder.save()
        order.orderStatus = data["order_status"]
        order.save()

        return JsonResponse({"success": True})
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def sync_bulk_buy_reponses(request):
    if request.method != "POST":
        return JsonResponse({'error':'POST only'}, status=405)
    token = request.headers.get('Authorization')
    if token != f'Bearer {SYNC_TOKEN}':
        return JsonResponse({'error':'Unauthorized'}, status=401)
    
    data = json.loads(request.body)
    try:
        bulk_buy_request_no = data['request_no']
        responding_fpo = data['fpo_username']
        response_date = data['response_date']
        bulk_buy_id = get_object_or_404(BulkBuy, bulkBuyNo = bulk_buy_request_no)
        fpo_id = get_object_or_404(CustomUser, username=responding_fpo)
        bb_response_instance, created = BulkBuyResponse.objects.update_or_create(
            bulkBuyID = bulk_buy_id,
            response_userID = fpo_id,
            defaults={
                "response_date" : response_date,
                "response_status" : True,
                "response_remark_date" : timezone.now()
            }
        )
        response_details = data['fpo_response_details_instance']
        for items in response_details:
            item_name = items['item_name']
            item_spec = items['item_spec']
            item_qty = items['item_qty']
            item_price = items['item_price']
            item_bid_price = items['bid_price']
            bb_details_instance = get_object_or_404(BulkBuyDetails, bulkBuyID=bulk_buy_id, itemName=item_name)
            BulkBuyResponseDetails.objects.update_or_create(
                bbrID = bb_response_instance,
                bbdID = bb_details_instance,
                defaults={
                    "itemPrice_indicative" : item_price,
                    "itemPrice_response" : item_bid_price,
                    "itemQty_indicative" : item_qty,
                }
            )
        return JsonResponse({'success':True},status=200)
    except Exception as e:
        print(str(e))
        return JsonResponse({'error':str(e)}, status=401)

@csrf_exempt
def push_bulk_buy_acceptance_to_onefpo(request,order_no):
    """
    Sync the accepted bulk buy response from the bulk buy requests
    """
    BASE_URL = settings.ONEFPO_SYNC_BASE_URL
    SYNC_URL = settings.ONEFPO_PUSH_ACCEPTED_BULK_ORDER_RESPONSE
    SYNC_TOKEN = settings.ONEFPO_SYNC_TOKEN

    accepted_bulk_buy_response_instance = get_object_or_404(BulkBuyResponse, bulkBuyID__bulkBuyNo = order_no, response_remark='Accepted')
    accepted_fpo_username = accepted_bulk_buy_response_instance.response_userID.username

    payload = {
        "bulkbuy_request_no":accepted_bulk_buy_response_instance.bulkBuyID.bulkBuyNo,
        "accepted_fpo_username":accepted_fpo_username
    }

    headers={
        "Authorization": f"Bearer {SYNC_TOKEN}",
        "Content-Type":"application/json"
    }

    try:
        response = requests.post(
            url = SYNC_URL,
            json = payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        if response.status_code == 200:
            return JsonResponse({'status':'ok'}, status=200)
        else:
            return JsonResponse({'status':'error'}, status=500)
    except Exception as e:
        print(str(e))
        return JsonResponse({'error':str(e)},status = 400)