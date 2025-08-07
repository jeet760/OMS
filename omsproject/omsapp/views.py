from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib import messages
from django.db import connection, transaction
from django.db.models import Q, Max, Min, Sum, Count, OuterRef, Subquery, F, Value
from django.db.models.functions import Concat
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from datetime import datetime
from .models import CustomUser, UserShippingAddresses, UserBillingAddresses, FPOServingAddresses, Login, Item, ItemStock, Order, OrderDetails, Cart, CartItem, OrderInvoice, OrderDelivery, BulkBuy, BulkBuyDetails, BulkBuyResponse, BulkBuyResponseDetails, SubOrder, FPOAuthorisationDocs, UserMessage, SchoolUDISE #LGDData
from .models import LIST_STATES, USERTYPES, GST_TREATMENT
from .forms import ItemForm, UserRegistrationForm, UserLoginForm, OrderForm, OrderDetailsForm, InvoiceForm, FPOAuthrisationForm, ItemImportExcelForm
import json
import requests
from .cart import Cart
from .deliveryschedule import DeliverySchedule
import razorpay
from urllib.parse import urlparse
import pandas as pd
import socket
import hmac
import hashlib
import random
from django.core.files.base import ContentFile
import base64


#region New index page and shop page
#Featured Products in the landing page
def featured_product(request):
    entered_pincode = request.GET.get('pincode')
    session_pincode = request.session.get('pincode')
    pincode = None

    if entered_pincode:
        pincode = entered_pincode
    elif session_pincode:
        pincode = session_pincode

    if pincode:
        request.session['pincode'] = pincode
    else:
        pincode = None

    if request.user.is_authenticated:
        if not pincode:
            pincode = request.user.pinCode
            request.session['pincode'] = pincode

    featureItems = Item.objects.filter(featureItem=True, userID_id__isActive=True, itemActive=True).order_by('-itemInStock')#featured items whose owner/seller is active and is in stock from seller's side
    #irrespective of the login status, the explicitly entered pincode will prevails
    if pincode:
        featureItems = featureItems.exclude(userID_id = request.user.pk).filter(userID_id__pinCode=pincode)

    #pagination in featured items
    paginator = Paginator(featureItems,12)
    page_number = request.GET.get('page')
    featureItems_page_obj = paginator.get_page(page_number)

    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()

    if pincode:
        #to display in the stats section
        veg_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Vegetables', userID_id__pinCode=pincode).__len__()
        fru_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Fruits', userID_id__pinCode=pincode).__len__()
        dai_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Dairy', userID_id__pinCode=pincode).__len__()
        spi_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Spices', userID_id__pinCode=pincode).__len__()
        cer_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Cereals', userID_id__pinCode=pincode).__len__()
        pul_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Pulses', userID_id__pinCode=pincode).__len__()
        ani_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Animal Sourced', userID_id__pinCode=pincode).__len__()
        for_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Forest Produces', userID_id__pinCode=pincode).__len__()
        pac_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Packaged Foods', userID_id__pinCode=pincode).__len__()
        oth_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Others', userID_id__pinCode=pincode).__len__()
    else:
        #to display in the stats section
        veg_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Vegetables').__len__()
        fru_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Fruits').__len__()
        dai_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Dairy').__len__()
        spi_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Spices').__len__()
        cer_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Cereals').__len__()
        pul_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Pulses').__len__()
        ani_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Animal Sourced').__len__()
        for_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Forest Produces').__len__()
        pac_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Packaged Foods').__len__()
        oth_value = Item.objects.filter(userID_id__isActive=True, itemActive=True, itemCat='Others').__len__()

    stats = [
        {"value": veg_value, "label": "Vegetables"},
        {"value": fru_value, "label": "Fruits"},
        {"value": dai_value, "label": "Dairy"},
        {"value": spi_value, "label": "Spices"},
        {"value": cer_value, "label": "Cereals"},
        {"value": pul_value, "label": "Pulses"},
        {"value": ani_value, "label": "Animal Sourced"},
        {"value": for_value, "label": "Forest Produces"},
        {"value": pac_value, "label": "Packaged Foods"},
        {"value": oth_value, "label": "Others"},
    ]

    fp_context = {
        'featureItems':featureItems,
        'featureItems_page_obj':featureItems_page_obj,
        'clicked':'Home',
        'pincode':pincode,
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price,
        'stats':stats
    }
    return render(request, 'featured-product.html', context=fp_context)

#shop
def marketplace(request):
    entered_pincode = request.GET.get('pincode')
    session_pincode = request.session.get('pincode')
    pincode = None

    if entered_pincode:
        pincode = entered_pincode
    elif session_pincode:
        pincode = session_pincode

    if pincode:
        request.session['pincode'] = pincode
    else:
        pincode = None

    if request.user.is_authenticated:
        if not pincode:
            pincode = request.user.pinCode
            request.session['pincode'] = pincode

    #all active and in stock items
    items = Item.objects.filter(userID_id__isActive=True, itemActive=True).order_by('-itemInStock')
    #irrespective the login status, the explicitly entered picode will previal    
    if pincode:
        items = items.exclude(userID_id = request.user.pk).filter(userID_id__pinCode=pincode)

    if request.GET.__len__() > 0:
        #data received from filter or from search box
        item_type= '' if request.GET.get('item_type')is None or request.GET.get('item_type') == '' else request.GET.get('item_type')
        fpo_selected = '' if request.GET.get('fpo_selected') is None or request.GET.get('fpo_selected') == '' else request.GET.get('fpo_selected')
        max_price = 0 if request.GET.get('max_price') is None or request.GET.get('max_price') == '' else request.GET.get('max_price')

        #searched item or item types/categories
        search = request.GET.get('search')

        if search is not None and search != '':
            items = items.filter(Q(itemName__icontains=search)|Q(itemCat__icontains=search))
        if item_type is not None and item_type != '':
            items = items.filter(itemCat__icontains=item_type)
        if fpo_selected is not None and fpo_selected != '':
            items = items.filter(userID__last_name__icontains=fpo_selected)
        if max_price is not None and max_price != 0:
            items = items.filter(itemPrice__range=(0,float(max_price)))

    fpos = CustomUser.objects.filter(userType='1',pinCode=pincode).exclude(pk=request.user.pk)
    
    paginator = Paginator(items,12)
    page_number = request.GET.get('page')
    items_page_obj = paginator.get_page(page_number)

    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()

    shop_context = {
        'items':items,
        'items_page_obj':items_page_obj,
        'fpos':fpos,
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price,
        'pincode':pincode
    }
    return render(request, 'shop.html', context=shop_context)

#item details while shopping
def item_details(request, item_id):
    user_type = ''
    user_name = 'Guest!'#display the username
    user_approved=''
    pincode = 'Pincode'
    if request.session.get('pincode') != '' and request.session.get('pincode') != None:
        pincode = request.session.get('pincode')

    item = get_object_or_404(Item, pk=item_id)
    pincode = item.userID.pinCode
    related_items = Item.objects.filter(itemCat = item.itemCat).filter(userID_id__pinCode=pincode).exclude(pk=item_id)
    counter = related_items.count()
    item_details_context = {
        'item':item,
        'related_items':related_items
    }
    return render(request, 'item-details.html', context = item_details_context)

#system checks whether the system is online or not
def is_online(host='api.postalpincode.in', port=443, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def PinCodeAPI(request, pincode):
    if is_online() == True:
        post_api = f'https://api.postalpincode.in/pincode/{pincode}'
        try:
            api_response = requests.get(post_api) 
            postalData = api_response.json()
            postalData_response = ''
            if postalData[0]['Status'] == 'Success':
                postoffice_data = postalData[0]['PostOffice']
                postalData_response = postoffice_data[0]['Name']+", "+postoffice_data[0]['Block']
            else:
                postoffice_data[0]['Message']
        except Exception as ex:
            print(ex)
            postalData_response = pincode
        return postalData_response
    else:
        messages.error(request, 'Failed to connect to internet!')

def shop_details(request, item_id):
    item = get_object_or_404(Item,pk=item_id)
    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()
    if request.user.is_authenticated:
        user_name=request.user.last_name
        pincode = request.session.get('pincode') #get the logged in user's pincode
        related_items = Item.objects.filter(itemCat = item.itemCat).filter(userID_id__pinCode=pincode)
    else:
        related_items = Item.objects.filter(itemCat = item.itemCat)
    related_items = related_items.exclude(userID_id=request.user.pk).order_by('itemID')

    #pagination in the landing page
    paginator = Paginator(related_items,12)
    page_number = request.GET.get('page')
    relatedItems_page_obj = paginator.get_page(page_number)

    user_name = 'Guest!'#display the username
    user_type = ''
    pincode='Pincode'
    if request.user.is_authenticated:
        user_name=request.user.last_name
        pincode = request.session.get('pincode')
        user_type=request.user.userType
    shop_details_context = {
        'item':item,
        #'related_items':related_items,
        'relatedItems_page_obj':relatedItems_page_obj,
        'login_user':user_name,
        'user_type':user_type,
        'pincode':pincode,
        'clicked':'Shop',
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price
    }
    return render(request, 'shop-details.html', shop_details_context)

def contact(request):
    qs = request.GET.get('q')
    if request.method == 'POST' and qs == 'msg':
        senderName=request.POST['senderName']
        senderEmail=request.POST['senderEmail']
        senderMsg=request.POST['senderMsg']
        UserMessage.objects.create(name=senderName,email=senderEmail,msg=senderMsg)
        return redirect('contact')
    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()
    user_name = 'Guest!'#display the username
    user_type =''
    user_approved = ''
    pincode='Pincode'
    pincode = request.session.get('pincode')
    if request.user.is_authenticated:
        user_name = request.user.last_name
        user_type = request.user.userType
        user_approved = request.user.userApproved
    contact_context = {
        'clicked':'Contact',
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price,
        'login_user':user_name,
        'pincode':pincode,
        'user_type':user_type,
        'user_approved':user_approved
    }
    return render(request, 'contact.html', contact_context)

def blog(request):
    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()
    blog_context = {
        'clicked':'Blog',
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price
    }
    return render(request, 'blog.html', blog_context)

def checkout(request):
    if request.user.is_authenticated:
        checkout_context = {
            'login_user' : request.user.last_name,
            'order_date':datetime.now,
            'order_amount':request.session['total_cart_price']
        }
        return render(request, 'checkout.html', context=checkout_context)
    else:
        return redirect('login')

def fpo_list(request):
    fpo = CustomUser.objects.filter(userType=1).exclude(pk=request.user.pk)
    return fpo

def error_404_view(request):
    return render(request, '404.html', {} )

def aboutus(request):
    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()
    aboutus_context = {
        'clicked':'About Us',
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price
    }
    return render(request, 'about-us.html', aboutus_context)

def privacypolicy(request):
    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()
    privacy_context = {
        'clicked':'Privacy Policy',
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price
    }
    return render(request, 'privacy-policy.html', privacy_context)

def deliverypolicy(request):
    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()
    delivery_context = {
        'clicked':'Delivery Policy',
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price
    }
    return render(request, 'delivery-policy.html', delivery_context)

def returnpolicy(request):
    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()
    return_context = {
        'clicked':'Return Policy',
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price
    }
    return render(request, 'return-policy.html', return_context)

def eula(request):
    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()
    eula_context = {
        'clicked':'End User',
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price
    }
    return render(request, 'eula.html', eula_context)

def testimonials(request):
    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()
    testimonials_context = {
        'clicked':'Testimonials',
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price
    }
    return render(request, 'testimonials.html', testimonials_context)

#endregion

#region Search Items
def SearchItems(request):
    items = Item.objects.filter(itemActive=True)
    context = {'count': items.count()}
    return render(request, 'index.html', context)

def SearchItemView(request):
    query = request.GET.get('search', '')
    items = Item.objects.filter(itemActive=True)
    if query:
        searchItem = items.filter(itemName__icontains = query)
    else:
        searchItem = []

    context = {'items':searchItem, 'count':items.count()}
    return render(request, 'search_results.html', context)
#endregion

#region Login, Logout and Registration and Password Reset
@login_required
def user_form(request):
    if request.user.is_authenticated:
        user = CustomUser.objects.filter(pk = request.user.pk)
        fpo_docs = FPOAuthorisationDocs.objects.filter(userID_id=request.user.pk)
    user_form_context = {
        'user':user,
        'fpo_docs':fpo_docs,
        'states':LIST_STATES,
        'gst_tmts': GST_TREATMENT
    }
    return render(request, 'user-form.html', context=user_form_context)

LIST_STATES = [
    ('', 'Select State'),
    ('28','Andhra Pradesh'),
    ('12','Arunachal Pradesh'),
    ('18','Assam'),
    ('10','Bihar'),
    ('22','Chhattisgarh'),
    ('30','Goa'),
    ('24','Gujarat'),
    ('6','Haryana'),
    ('2','Himachal Pradesh'),
    ('20','Jharkhand'),
    ('29','Karnataka'),
    ('32','Kerala'),
    ('23','Madhya Pradesh'),
    ('27','Maharashtra'),
    ('14','Manipur'),
    ('17','Meghalaya'),
    ('15','Mizoram'),
    ('13','Nagaland'),
    ('21','Odisha'),
    ('3','Punjab'),
    ('8','Rajasthan'),
    ('11','Sikkim'),
    ('33','Tamil Nadu'),
    ('36','Telangana'),
    ('16','Tripura'),
    ('9','Uttar Pradesh'),
    ('5','Uttarakhand'),
    ('19','West Bengal'),
    ('35','Andaman And Nicobar Islands [UT]'),
    ('4','Chandigarh [UT]'),
    ('7','Delhi [UT]'),
    ('1','Jammu And Kashmir [UT]'),
    ('37','Ladakh [UT]'),
    ('31','Lakshadweep [UT]'),
    ('34','Puducherry [UT]'),
    ('38','The Dadra And Nagar Haveli And Daman And Diu [UT]'),
]

LIST_USERTYPES = [
    ('1','FPO'),
    ('2','Business'),
    ('3','School'),
    ('4','Overseas'),
    ('5','Individual'),
]

def fetch_school(request, udise):
    """To fetch the details of the school in the registration form"""
    school = get_object_or_404(SchoolUDISE, udise_code=udise)
    school_name = school.school_name
    list_state_reverse_dict = {k: v for v, k in LIST_STATES}
    state_value = list_state_reverse_dict.get(school.state_name)
    district_name = school.district_name
    sub_dist_name = school.sub_dist_name
    village_name = school.village_name
    json_response = {
        'school_name':school_name,
        'state_name':state_value,
        'district_name':district_name,
        'sub_dist_name':sub_dist_name,
        'village_name':village_name
    }
    return JsonResponse(json_response)

def registration_form(request):
    form = UserRegistrationForm()#new register point: opening the registratino page without login
    user_name = 'Guest!'
    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()
    register_context = {
        'userform': form,
        'login_user':user_name,
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price,
        'states':LIST_STATES,
        'gst_tmts':GST_TREATMENT,
        'user_types':USERTYPES,
    }
    return render(request, 'register.html', context=register_context)

def create_fpo_regn_id(state_code,district_code,subdist_code):
    num = random.randint(1,99)
    regn_id = ''
    if num < 10:
        regn_id = state_code+district_code+subdist_code+'0'+str(num)
    else:
        regn_id = state_code+district_code+subdist_code+str(num)
    return regn_id

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)#Point: After clicking register button
        if request.user.is_authenticated == False: #update == None:#New registration
            if form.is_valid():
                if request.POST['userType'] == '3':
                    udise_exists = SchoolUDISE.objects.filter(udise_code=request.POST['udise_code']).exists()
                    if udise_exists == False:
                        messages.error(request,'Invalid UDISE Code!\nPlease use valid UDISE code.')
                        return redirect('register')
                    
                    check_reg = CustomUser.objects.filter(udise_code=request.POST['udise_code']).exists()
                    if check_reg:
                        messages.error(request, 'UDISE Code exists! Please login using UDISE Code.')
                        return redirect('register')
                    else:
                        user = form.save(param_password=request.POST['udise_code'])
                        messages.success(request,f'You can use your phone number {request.POST['phone']} or UDISE Code {request.POST['udise_code']} as Username.\nPassword is the UDISE Code.')
                elif request.POST['userType'] == '1':
                    regn_no = create_fpo_regn_id(request.POST['userState'],request.POST['userDistrict'],request.POST['userCity'])
                    user = form.save(param_password=request.POST['phone'], commit=False)
                    user.username = regn_no
                    user.save()
                    messages.success(request,f'Your Registration Code is {regn_no}.\nYou can also use this code or phone number {request.POST['phone']} as Username.\nPassword is your phone number.')
                else:
                    user = form.save(param_password=request.POST['phone'])
                    messages.success(request,f'You can use phone number {request.POST['phone']} as Username.\nPassword is your phone number.')
                contact_person = user.last_name
                contact_no = user.phone

                pincode_lat_lon_data = fetch_lat_lon_from_pincode_api(user.pinCode)
                loc_lat = pincode_lat_lon_data['lat']
                loc_long = pincode_lat_lon_data['lon']
                # loc_lat = 20.9517
                # loc_long = 85.0985
                if user.userType == '3':
                    school = get_object_or_404(SchoolUDISE, udise_code=user.udise_code)
                    loc_lat=school.loc_lat
                    loc_long=school.loc_long
                    
                lgd_data = fetch_lgd_data_from_api(user.userState, user.userDistrict, user.userCity)
                userCity_name = lgd_data['sub_dist_name']
                userDistrict_name = lgd_data['district_name']
                userState_name = lgd_data['state_name']

                CustomUser.objects.filter(pk=user.id).update(userCity_name=userCity_name, userDistrict_name=userDistrict_name, userState_name=userState_name, bill_address_lat = loc_lat, bill_address_long = loc_long, ship_address_lat = loc_lat, ship_address_long = loc_long)
                UserBillingAddresses.objects.create(userID_id=user.pk,userAddress=user.userAddress, userCity=user.userCity, userCity_name=userCity_name, userDistrict=user.userDistrict, userDistrict_name=userDistrict_name, userState=user.userState, userState_name=userState_name, pinCode=user.pinCode, contactPerson=contact_person, contactNo=contact_no, address_lat=loc_lat, address_long=loc_long, setDefault=True)
                UserShippingAddresses.objects.create(userID_id=user.pk,userAddress1=user.userAddress, userCity1=user.userCity, userCity1_name=userCity_name, userDistrict1=user.userDistrict, userDistrict1_name=userDistrict_name, userState1=user.userState, userState1_name=userState_name, pinCode1=user.pinCode, contactPerson1=contact_person, contactNo1=contact_no, address_lat1=loc_lat, address_long1=loc_long, setDefault=True)
                if user.userType == '1':
                    FPOServingAddresses.objects.create(userID_id=user.pk, userAddress1=user.userAddress, userCity1=user.userCity, userCity1_name=userCity_name, userDistrict1=user.userDistrict, userDistrict1_name=userDistrict_name, userState1=user.userState, userState1_name=userState_name, pinCode1=user.pinCode, contactPerson1=contact_person, contactNo1=contact_no, address_lat1=loc_lat, address_long1=loc_long, isActive=True)
                if user.userType != '1':
                    CustomUser.objects.filter(pk=user.id).update(userApproved=True,approvedOn=datetime.today(),isActive=True,activatedOn=datetime.today())
                return redirect('login')  # Redirect to a home page
            else:
                print(form.errors)
                errors = form.errors.get_json_data()
                for field, field_errors in errors.items():
                    for error in field_errors:
                        messages.error(request, f"{field.capitalize()}: {error['message']}")
                return redirect('register')
        else:
            return redirect('register')
    else:
        return redirect('register')

def profile_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)#Point: After clicking register button
        if request.user.is_authenticated == False: #update == None:#New registration
            if form.is_valid():
                user = form.save(param_password=request.POST['phone'])
                login(request, user)
                user_name = request.user.last_name
                return redirect('index')  # Redirect to a home page
        else:
            userInstance = get_object_or_404(CustomUser, id=request.user.pk)
            form = UserRegistrationForm(request.POST, instance=userInstance)
            user = form.save(param_password=request.POST['phone'])
            login(request, user)
            user_name = request.user.last_name
            pass
        return redirect('profile')
    else:
        if request.user.is_authenticated:#Point: After logging in trying to edit the profile
            if request.user.userApproved:
                user = request.user
                user_name = request.user.last_name
                userInstance = get_object_or_404(CustomUser, id=request.user.pk)
                form = UserRegistrationForm(instance=userInstance)
                try:
                    fpo_docs = get_object_or_404(FPOAuthorisationDocs, userID_id=request.user.pk)
                except:
                    fpo_docs = ''
            else:
                return redirect('profile-auth')
                #return JsonResponse({'approve':'false'})
        else:
            return redirect('login')
    if userInstance:
        user_type = userInstance.userType
    else:
        user_type=''
    shipping_addresses = UserShippingAddresses.objects.filter(userID = request.user.pk)
    billing_addresses = UserBillingAddresses.objects.filter(userID = request.user.pk)
    serving_addresses = FPOServingAddresses.objects.filter(userID=request.user.pk)
    contact_person = [CustomUser.objects.get(pk=request.user.pk).contactPerson, CustomUser.objects.get(pk=request.user.pk).contactNo]
    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()
    register_context = {
        'userform': form,
        'user':user,
        'contact_person':contact_person,
        'login_user':user_name,
        'user_type':user_type,
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price,
        'states':LIST_STATES,
        'gst_tmts':GST_TREATMENT,
        'user_types':USERTYPES,
        'shipping_addresses':shipping_addresses,
        'billing_addresses':billing_addresses,
        'serving_addresses':serving_addresses,
        'add_address_from':'userform',
        'fpo_docs':fpo_docs
    }
    return render(request, 'user-form.html', context=register_context)

def fpo_auth(request):
    if request.user.is_authenticated:
        user_approved = request.user.userApproved
        login_user = request.user.last_name
        auth_details = FPOAuthorisationDocs.objects.filter(userID_id=request.user.pk)
        if auth_details.exists():
            auth_form = FPOAuthrisationForm(instance=auth_details.first())
        else:
            auth_form = FPOAuthrisationForm()
        fpo_auth_context ={
            'auth_form':auth_form,
            'auth_details':auth_details,
            'user_approved':user_approved,
            'login_user':login_user
        }
    else:
        return redirect('login')
    return render(request, 'fpo-auth.html', context=fpo_auth_context)

def upload_fpo_docs(request):
    if request.method == 'POST':
        fpo_auth_instance = FPOAuthorisationDocs.objects.filter(userID_id=request.user.pk).first()
        auth_form = FPOAuthrisationForm(request.POST, request.FILES, instance=fpo_auth_instance)
        if auth_form.is_valid():
            if request.user.is_authenticated:
                user_id = request.user.pk
                fpo_auth = auth_form.save(userID = user_id)
            else:
                return redirect('login')
        else:
            return redirect('profile-auth')
    else:
        return redirect('profile-auth')
    return redirect('index')

def approve_user(request, userID):
    CustomUser.objects.filter(pk=userID).update(userApproved=True, isActive=True, approvedOn=datetime.now())
    return redirect('admin-master')

def verify_fpo(request, userID):
    fpo_docs=FPOAuthorisationDocs.objects.filter(userID_id=userID)
    fpo_doc = request.GET.get('doc')
    fpo_action_get = request.GET.get('action')
    remark = request.GET.get('remark')
    fpo_action = True if fpo_action_get == 'verify' else False

    if fpo_doc == 'br':
        fpo_docs.update(br_verified=fpo_action, br_remark=remark, br_verified_on=datetime.today())
    elif fpo_doc == 'cin':
        fpo_docs.update(cin_verified=fpo_action, cin_remark=remark, cin_verified_on=datetime.today())
    elif fpo_doc == 'pan':
        fpo_docs.update(pan_verified=fpo_action, pan_remark=remark, pan_verified_on=datetime.today())
    elif fpo_doc == 'bank':
        fpo_docs.update(bank_verified=fpo_action, bank_remark=remark, bank_verified_on=datetime.today())
    elif fpo_doc == 'fssai':
        fpo_docs.update(fssai_verified=fpo_action, fssai_remark=remark, fssai_verified_on=datetime.today())
    elif fpo_doc == 'gst':
        fpo_docs.update(gst_verified=fpo_action, gst_remark=remark, gst_verified_on=datetime.today())
    elif fpo_doc == 'apmc':
        fpo_docs.update(apmc_verified=fpo_action, apmc_remark=remark, apmc_verified_on=datetime.today())
    elif fpo_doc == 'exim':
        fpo_docs.update(exim_verified=fpo_action, exim_remark=remark, exim_verified_on=datetime.today())

    fpo_form = FPOAuthrisationForm(instance=fpo_docs.first())
    fpo_check = fpo_approve_check(userID)
    #print(fpo_check)
    verify_context = {
        'fpo_docs':fpo_docs,
        'auth_form':fpo_form,
        'fpo_user':userID,
        'fpo_check':fpo_check
    }
    return render(request, 'fpo-verify.html', context=verify_context)

def fpo_approve_check(userID):
    user = get_object_or_404(CustomUser,pk=userID)
    fpo_instance_list = [
        {'column':'board_resolution', 'value':''},
        {'column':'cin', 'value':''},
        {'column':'pan', 'value':''},
        {'column':'bank', 'value':''},
        {'column':'fssai', 'value':''},
        {'column':'gst', 'value':''},
        {'column':'apmc', 'value':''},
        {'column':'exim', 'value':''},
    ]

    if user.userType == '1':
        try:
            fpo_instance = get_object_or_404(FPOAuthorisationDocs,userID_id=userID)
            column_counter = 0
            value_counter = 0
            for instance in fpo_instance_list:
                for field in fpo_instance._meta.get_fields():
                    if hasattr(field, 'attname'):  # skip related fields, M2M, etc.
                        if instance['column'] == field.name:
                            column_value = getattr(fpo_instance, field.name, None)
                            if hasattr(column_value, 'name') and column_value.name:
                                column_counter+=1
                                #print(f"{field.name}: {column_value.name}")
                                
                            field_name = 'br_verified' if field.name == 'board_resolution' else field.name+'_verified'
                            field_value = getattr(fpo_instance, field_name, None)
                            if field_value == True:
                                value_counter+=1
            #print(f"Field: {column_counter} → Value: {value_counter}")
            if column_counter == value_counter:
                return True
            else:
                return False
        except:
            fpo_instance = None
            return False

def activate_user(request, userID, activate):
    referer = request.META.get('HTTP_REFERER')
    parsed_url = urlparse(referer)
    path_only = parsed_url.path  # e.g., /some/path/
    if activate == 'false':
        CustomUser.objects.filter(pk=userID).update(isActive=False,activatedOn=datetime.now())
    else:
        CustomUser.objects.filter(pk=userID).update(isActive=True,activatedOn=datetime.now())
    if path_only == '/admin-master/':
        return redirect('admin-master')
    else:
        return redirect('logout')

def change_mobile_number(request, new_phone):
    if request.user.is_authenticated:
        exist_phone = get_object_or_404(CustomUser, pk=request.user.pk).phone
        update_records = CustomUser.objects.filter(pk = request.user.pk,phone = exist_phone).update(phone=new_phone)
    return redirect('user-form')

def add_address(request):
    if request.user.is_authenticated:
        userID=request.user.pk
        userAddress = request.POST.get('userAddress')
        userCity_code = request.POST.get('userCity')
        userDistrict_code = request.POST.get('userDistrict')
        userState_code = request.POST.get('userState')
        lgd_data = fetch_lgd_data_from_api(userState_code, userDistrict_code, userCity_code)
        userCity_name = lgd_data['sub_dist_name']
        userDistrict_name = lgd_data['district_name']
        userState_name = lgd_data['state_name']
        pinCode = request.POST.get('pinCode')
        contactPerson = request.POST.get('contactPerson')
        contactNo = request.POST.get('contactNo')
        setDefault = True
        type_of_address = request.POST.get('selectAddress')
        lat_lon = fetch_lat_lon_from_pincode_api(pinCode)
        pincode_lat = lat_lon['lat']
        pincode_lon = lat_lon['lon']
        if type_of_address == 'bill':
            UserBillingAddresses.objects.filter(userID_id=userID).update(setDefault=False)
            UserBillingAddresses.objects.get_or_create(userID_id=userID, userAddress=userAddress, userCity=userCity_code, userCity_name=userCity_name, userDistrict=userDistrict_code, userDistrict_name=userDistrict_name, userState=userState_code, userState_name=userState_name, pinCode=pinCode, contactNo=contactNo, contactPerson=contactPerson, address_lat=pincode_lat, address_long=pincode_lon, setDefault=setDefault)
        elif type_of_address == 'ship':
            UserShippingAddresses.objects.filter(userID_id=userID).update(setDefault=False)
            UserShippingAddresses.objects.get_or_create(userID_id=userID, userAddress1=userAddress, userCity1=userCity_code, userCity1_name=userCity_name, userDistrict1=userDistrict_code, userDistrict1_name=userDistrict_name, userState1=userState_code, userState1_name=userState_name, pinCode1=pinCode, contactNo1=contactNo, contactPerson1=contactPerson, address_lat1=pincode_lat, address_long1=pincode_lon, setDefault=setDefault)
        elif type_of_address == 'serv':
            FPOServingAddresses.objects.get_or_create(userID_id=userID, userAddress1=userAddress, userCity1=userCity_code, userCity1_name=userCity_name, userDistrict1=userDistrict_code, userDistrict1_name=userDistrict_name, userState1=userState_code, userState1_name=userState_name, pinCode1=pinCode, contactNo1=contactNo, contactPerson1=contactPerson, address_lat1=pincode_lat, address_long1=pincode_lon)
        elif type_of_address == 'both':
            UserBillingAddresses.objects.filter(userID_id=userID).update(setDefault=False)
            UserBillingAddresses.objects.get_or_create(userID_id=userID, userAddress=userAddress, userCity=userCity_code, userDistrict=userDistrict_code,userState=userState_code,pinCode=pinCode,contactNo=contactNo, contactPerson=contactPerson, address_lat=pincode_lat, address_long=pincode_lon, setDefault=setDefault)
            UserShippingAddresses.objects.filter(userID_id=userID).update(setDefault=False)
            UserShippingAddresses.objects.get_or_create(userID_id=userID, userAddress1=userAddress, userCity1=userCity_code, userDistrict1=userDistrict_code,userState1=userState_code,pinCode1=pinCode, contactNo1=contactNo, contactPerson1=contactPerson, address_lat1=pincode_lat, address_long1=pincode_lon, setDefault=setDefault)
    
        referer = request.META.get('HTTP_REFERER')
        parsed_url = urlparse(referer)
        path_only = parsed_url.path  # e.g., /some/path/
        if path_only == '/cart/':
            return redirect('cart')    
        else:
            return redirect('user-form')
    else:
        return redirect('login')

def update_profile(request):
    if request.user.is_authenticated and request.method == 'POST':
        userID = request.user.pk
        last_name = request.POST.get('last_name')
        email=request.POST.get('email')
        phone1 = request.POST.get('phone1')
        CustomUser.objects.filter(pk=userID).update(last_name=last_name,email=email,phone1=phone1)
    return redirect('user-form')

def fetch_lgd_data_from_api(state_code,district_code,sub_dist_code):
    api = f'https://api.data.gov.in/resource/6be51a29-876a-403a-a6da-42fde795e751?api-key=579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b&format=json&limit=1000&filters%5Bstate_code%5D={state_code}&filters%5Bdistrict_code%5D={district_code}&filters%5Bsubdistrict_code%5D={sub_dist_code}'
    api_response = requests.get(api) 
    lgd_data = api_response.json()
    state_name = lgd_data['records'][0]['state_name_english']
    district_name = lgd_data['records'][0]['district_name_english']
    sub_dist_name = lgd_data['records'][0]['subdistrict_name_english']
    return_context = {
        'state_name':state_name,
        'district_name':district_name,
        'sub_dist_name':sub_dist_name,
        'state_code':state_code,
        'district_code':district_code,
        'sub_dist_code':sub_dist_code
    }
    return return_context

def fetch_lat_lon_from_pincode_api(pincode):
    api = f'https://api.data.gov.in/resource/5c2f62fe-5afa-4119-a499-fec9d604d5bd?api-key=579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b&format=json&filters%5Bpincode%5D={pincode}'
    api_response = requests.get(api)
    pincode_data = api_response.json()
    lat = pincode_data['records'][0]['latitude']
    lon = pincode_data['records'][0]['longitude']
    if lat == 'NA':
        if pincode_data['count'] > 1:
            lat = pincode_data['records'][1]['latitude']
            lon = pincode_data['records'][1]['longitude']
        else:
            lat = 0.0
            lon = 0.0

    lat_lon_context = {
        'lat':lat,
        'lon':lon
    }
    return lat_lon_context

def fetch_address(request, id):
    if request.user.is_authenticated:
        q = request.GET.get('q')
        if q == 'bill':
            address = get_object_or_404(UserBillingAddresses, pk=id)
            userID = address.userID.pk
            userAddress = address.userAddress
            userCity=address.userCity
            userCity_name=address.userCity_name
            userDistrict = address.userDistrict
            userDistrict_name = address.userDistrict_name
            userState = address.userState
            userState_name = address.userState_name
            pinCode = address.pinCode
            contactPerson = address.contactPerson
            contactNo = address.contactNo
        elif q == 'ship':
            address = get_object_or_404(UserShippingAddresses, pk=id)
            userID = address.userID.pk
            userAddress = address.userAddress1
            userCity=address.userCity1
            userCity_name=address.userCity1_name
            userDistrict = address.userDistrict1
            userDistrict_name = address.userDistrict1_name
            userState = address.userState1
            userState_name = address.userState1_name
            pinCode = address.pinCode1
            contactPerson = address.contactPerson1
            contactNo = address.contactNo1
        elif q == 'serv':
            address = get_object_or_404(FPOServingAddresses, pk=id)
            userID = address.userID.pk
            userAddress = address.userAddress1
            userCity=address.userCity1
            userCity_name=address.userCity1_name
            userDistrict = address.userDistrict1
            userDistrict_name = address.userDistrict1_name
            userState = address.userState1
            userState_name = address.userState1_name
            pinCode = address.pinCode1
            contactPerson = address.contactPerson1
            contactNo = address.contactNo1

        address_context = {
            'userID':userID,
            'userAddress':userAddress,
            'userCity':userCity,
            'userCity_name':userCity_name,
            'userDistrict':userDistrict,
            'userDistrict_name':userDistrict_name,
            'userState':userState,
            'userState_name':userState_name,
            'pinCode':pinCode,
            'contactPerson':contactPerson,
            'contactNo':contactNo,
            'addressID':id
        }
    return JsonResponse({'address_context':address_context})

def update_billiing_address(request, id):
    if request.user.is_authenticated and request.method == 'POST':
        userID = request.user.pk
        id=request.POST.get('addressID')
        userAddress = request.POST.get('userAddress')
        userCity_code=request.POST.get('userCity')
        userDistrict_code = request.POST.get('userDistrict')
        userState_code = request.POST.get('userState')
        lgd_data = fetch_lgd_data_from_api(userState_code, userDistrict_code, userCity_code)
        userCity_name = lgd_data['sub_dist_name']
        userDistrict_name = lgd_data['district_name']
        userState_name = lgd_data['state_name']
        pinCode = request.POST.get('pinCode')
        contactPerson= request.POST.get('contactPerson')
        contactNo = request.POST.get('contactNo')
        UserBillingAddresses.objects.filter(pk=id, userID_id=userID).update(userAddress=userAddress, userCity=userCity_code,userCity_name=userCity_name, userDistrict=userDistrict_code, userDistrict_name=userDistrict_name, userState=userState_code, userState_name=userState_name, pinCode=pinCode, contactPerson=contactPerson, contactNo=contactNo)
    return redirect('user-form')

def update_shipping_address(request, id):
    if request.user.is_authenticated and request.method == 'POST':
        userID = request.user.pk
        id=request.POST.get('addressID1')
        userAddress = request.POST.get('userAddress')
        userCity_code=request.POST.get('userCity')
        userDistrict_code = request.POST.get('userDistrict')
        userState_code = request.POST.get('userState')
        lgd_data = fetch_lgd_data_from_api(userState_code, userDistrict_code, userCity_code)
        userCity_name = lgd_data['sub_dist_name']
        userDistrict_name = lgd_data['district_name']
        userState_name = lgd_data['state_name']
        pinCode = request.POST.get('pinCode')
        contactPerson= request.POST.get('contactPerson1')
        contactNo = request.POST.get('contactNo1')
        UserShippingAddresses.objects.filter(pk=id, userID_id=userID).update(userAddress1=userAddress, userCity1=userCity_code, userCity1_name=userCity_name, userDistrict1=userDistrict_code, userDistrict1_name=userDistrict_name, userState1=userState_code, userState1_name=userState_name, pinCode1=pinCode, contactPerson1=contactPerson, contactNo1=contactNo)
    return redirect('user-form')

def update_serving_address(request,id):
    if request.user.is_authenticated and request.method == 'POST':
        userID = request.user.pk
        id=request.POST.get('addressID2')
        userAddress = request.POST.get('userAddress')
        userCity_code=request.POST.get('userCity')
        userDistrict_code = request.POST.get('userDistrict')
        userState_code = request.POST.get('userState')
        lgd_data = fetch_lgd_data_from_api(userState_code, userDistrict_code, userCity_code)
        userCity_name = lgd_data['sub_dist_name']
        userDistrict_name = lgd_data['district_name']
        userState_name = lgd_data['state_name']
        pinCode = request.POST.get('pinCode')
        contactPerson= request.POST.get('contactPerson2')
        contactNo = request.POST.get('contactNo2')
        FPOServingAddresses.objects.filter(pk=id, userID_id=userID).update(userAddress1=userAddress, userCity1=userCity_code, userCity1_name=userCity_name, userDistrict1=userDistrict_code, userDistrict1_name=userDistrict_name, userState1=userState_code, userState1_name=userState_name, pinCode1=pinCode, contactPerson1=contactPerson, contactNo1=contactNo)
    return redirect('user-form')

def set_default_address(request, id):
    if request.user.is_authenticated:
        userID = request.user.pk
        type_of_address = request.GET['q']
        if type_of_address == 'bill':
            UserBillingAddresses.objects.filter(userID_id=userID).update(setDefault=False)
            UserBillingAddresses.objects.filter(pk=id, userID_id=userID).update(setDefault=True)
            bill_address = get_object_or_404(UserBillingAddresses, pk=id)
            CustomUser.objects.filter(id=userID).update(userAddress=bill_address.userAddress,userCity=bill_address.userCity,userState=bill_address.userState,pinCode=bill_address.pinCode)
        else:
            UserShippingAddresses.objects.filter(userID_id=userID).update(setDefault=False)
            UserShippingAddresses.objects.filter(pk=id, userID_id=userID).update(setDefault=True)
            ship_address = get_object_or_404(UserShippingAddresses, pk=id)
            CustomUser.objects.filter(id=userID).update(userAddress1=ship_address.userAddress1,userCity1=ship_address.userCity1,userState1=ship_address.userState1,pinCode1=ship_address.pinCode1)
    return redirect('user-form')    

def change_status_serving_address(request,id):
    if request.user.is_authenticated:
        userID = request.user.pk
        checkStatus = get_object_or_404(FPOServingAddresses,pk=id).isActive
        if checkStatus == True:
            FPOServingAddresses.objects.filter(userID_id=userID,pk=id).update(isActive=False)
        else:
            FPOServingAddresses.objects.filter(userID_id=userID,pk=id).update(isActive=True)
    return redirect('user-form')

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.changed_data.__len__() == 0:
            return redirect('login')#render(request, 'login.html', {'loginform': form})
        if form.is_valid:
            username = request.POST['username']
            password = request.POST['password']
            try:
                user_login = authenticate(request, username=username, password=password)
                if user_login:
                    if user_login.isActive == False:
                        messages.error(request, 'Your Account is not active! Please, contact administrator to activate your account.')
                    else:
                        login(request, user_login)
                        if user_login.userType == '0' and user_login.is_superuser:
                            return redirect('admin-master')
                        elif user_login.userType == '1':
                            if user_login.userApproved:
                                return redirect('dashboard')
                            else:
                                return redirect('profile-auth')
                        else:
                            return redirect('index')
                else:
                    messages.error(request, 'Incorrect Username or Password!\nPlease try again.')
            except Exception as ex:
                print(ex)
                messages.error(request, 'User does not exist!\nPlease check username and password.')
                #return redirect('login')
        else:
            form = UserLoginForm()
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'loginform': form, 'login_user':'Guest!'})

def forgot_password(request):
    return render(request, 'reset_password.html', {})

def reset_password_form(request):
    if request.user.is_authenticated:
        username = request.user.username
        password = request.user.password
        phone = request.user.phone
        email = request.user.email
        reset_password_context = {
            'username':username,
            'password':password,
            'phone':phone,
            'email':email,
        }
        return render(request, 'reset_password.html', context=reset_password_context)
    else:
        return render(request, 'reset_password.html', {})
    

def reset_password(request):
    if request.method == 'POST':
        param_username = request.POST.get('username')
        param_password = request.POST.get('password')
        user = get_object_or_404(CustomUser,username=param_username)
        user.set_password(param_password)
        user.save()
        return redirect('login')
    else:
        return render(request, 'reset_password.html', {})


@login_required
def logout_view(request):
    request.session.flush()
    logout(request)
    return redirect('index')
#endregion

#region Admin Consoles (application and system admins)
def admin_console(request):
    if request.user.is_authenticated:
        user = request.user
        last_name = request.user.last_name

    console_context = {
        'login_user':last_name,
        'user':user
    }
    return render(request, 'admin-console.html', console_context)

@login_required
def track_coordinate(request):
    address_qs = UserBillingAddresses.objects.values('userCity','address_lat','address_long', name=F('userID__last_name')).exclude(userID_id=1).exclude(address_lat=None).exclude(address_lat=0)
    coordinates = list(address_qs)
    return JsonResponse({'coordinates':coordinates})

def show_fpo_customers_in_map(request):
    #parameters from the form
    user_type = request.GET.get('type')
    serving_area = request.GET.get('area')
    serving_area_code = request.GET.get('code')
    searched_customer = request.GET.get('cust')

    all_customers = CustomUser.objects.all()

    #logged in FPO data
    fpo_user_id = request.user.pk
    fpo_name = get_object_or_404(CustomUser, id=fpo_user_id).last_name
    fpo_lat= get_object_or_404(CustomUser, id=fpo_user_id).bill_address_lat #21.2634154
    fpo_long = get_object_or_404(CustomUser, id=fpo_user_id).bill_address_long #85.8801451
    fpo_icon = 'black'
    fpo_dist = get_object_or_404(FPOServingAddresses, userID_id=fpo_user_id, userCity1=serving_area_code).userDistrict1_name
    fpo_subdist = serving_area

    #all customers who have ordered and their orders have been invoiced or delivered
    customer_user_ids = SubOrder.objects.values('customerID_id',name=F('customerID_id__last_name'),user_type=F('customerID_id__userType')).filter(vendorID_id = fpo_user_id, customerID_id__userType=user_type).filter(Q(orderStatus='Invoiced')|Q(orderStatus='Delivered'))


    #to contain all data to plot on map
    map_data = []
    map_data.append(
        {
            'name':fpo_name, 
            'address_lat':fpo_lat, 
            'address_long':fpo_long, 
            'order_count':0, 
            'icon':fpo_icon,
            'village':'',
            'students':0
        }
    )
    
    school_counts = 0
    ordering_school_counts = 0
    registered_schools_counts = 0
    #checking the user type
    if user_type == '1':#fpo
        all_registered_fpo_ids = all_customers.filter(userType=user_type)
    elif user_type == '2':#business
        all_registered_biz_ids = all_customers.filter(userType=user_type)
    elif user_type == '3':#school
        all_registered_schools_ids = all_customers.filter(userType=user_type)#registered schools
        registered_schools_counts = all_registered_schools_ids.count()
        #if registered_schools_counts > 0:
        school_context = plot_schools_on_map(map_data, all_registered_schools_ids, customer_user_ids, fpo_dist, fpo_subdist, school_name=searched_customer)
        map_data = school_context['map_data']
        school_counts = school_context['school_counts']
        ordering_school_counts = school_context['ordering_school_counts']
    elif user_type == '4':#overseas
        all_registered_overseas_ids = all_customers.filter(userType=user_type)
    elif user_type == '5':#individual
        all_registered_indv_ids = all_customers.filter(userType=user_type)
        registered_indvs_count = all_registered_indv_ids.count()
        registered_schools_counts = registered_indvs_count
        if registered_schools_counts > 0:
            indv_context = plot_individuals_on_map(map_data, all_registered_indv_ids, customer_user_ids)
            map_data = indv_context['map_data']
            school_counts = indv_context['indv_counts']
            ordering_school_counts = indv_context['ordering_indv_counts']


    return JsonResponse({'coordinates':map_data, 'total_schools':school_counts, 'registered_schools':registered_schools_counts, 'ordering_schools':ordering_school_counts})

def plot_schools_on_map(map_data, all_registered_schools_ids, customer_user_ids, district_name, sub_dist_name, school_name=None):
    #fetch all the subdistrict names from SchooUDISE and get the relevant name for given parameter of sub_dist_name and dist_name
    udise_data = SchoolUDISE.objects.all()
    udise_districts = list(udise_data.filter(state_code=21).values_list('district_name', flat=True).distinct())
    udise_subdists = list(udise_data.filter(state_code=21).filter(district_name=district_name).exclude(sub_dist_name='').values_list('sub_dist_name', flat=True).distinct())

    relevant_district = fuzzy_search(district_name, udise_districts)[0]
    relevant_subdist = fuzzy_search(sub_dist_name, udise_subdists)[0]

    #fetch all schools in the area, then fetch the registered schools, then the ordering schools
    all_schools = SchoolUDISE.objects.all().filter(district_name=relevant_district, sub_dist_name=relevant_subdist)#all schools
    if school_name is not None:
        all_schools = all_schools.filter(school_name__icontains = school_name)
    school_counts = all_schools.count()
    for school in all_schools:
        map_data.append(
            {
                'name':school.school_name, 
                'address_lat':school.loc_lat, 
                'address_long':school.loc_long, 
                'order_count':0, 
                'icon':'yellow',
                'village':school.village_name,
                'students':school.total_students
            }
        )

    ordering_school_counts = 0
    for school in all_registered_schools_ids:
        school_id = school.id
        school_name = school.last_name
        school_village = school.userAddress
        total_students = get_object_or_404(SchoolUDISE, udise_code=school.udise_code).total_students
        address_lat = get_object_or_404(UserBillingAddresses,userID_id=school_id, setDefault=True).address_lat
        address_long = get_object_or_404(UserBillingAddresses,userID_id=school_id, setDefault=True).address_long
        order_count = 0
        icon = 'red'
        for customer in customer_user_ids:
            customer_id = customer['customerID_id']
            if school_id == customer_id:#schools those have ordered and their orders have been delivered/invoiced
                ordering_school_counts+=1
                order_count = SubOrder.objects.values('suborderID').filter(customerID_id=customer_id).count()
                icon = 'green'
        map_data.append(
            {
                'name':school_name, 
                'address_lat':address_lat, 
                'address_long':address_long, 
                'order_count':order_count, 
                'icon':icon,
                'village':school_village,
                'students':total_students
            }
        )

    return_context = {
        'map_data':map_data,
        'school_counts':school_counts,
        'ordering_school_counts':ordering_school_counts
    }
    return return_context

def plot_individuals_on_map(map_data, all_registered_indv_ids, customer_user_ids):
    ordering_indv_counts = 0
    for indv in all_registered_indv_ids:
        indv_id = indv.id
        indv_name = indv.last_name
        address_lat = get_object_or_404(UserBillingAddresses,userID_id=indv_id).address_lat
        address_long = get_object_or_404(UserBillingAddresses,userID_id=indv_id).address_long
        order_count = 0
        icon = 'red'
        for customer in customer_user_ids:
            customer_id = customer['customerID_id']
            if indv_id == customer_id:#schools those have ordered and their orders have been delivered/invoiced
                ordering_indv_counts+=1
                order_count = SubOrder.objects.values('suborderID').filter(customerID_id=customer_id).count()
                icon = 'green'
        map_data.append(
            {
                'name':indv_name, 
                'address_lat':address_lat, 
                'address_long':address_long, 
                'order_count':order_count, 
                'icon':icon
            }
        )
        return_context = {
            'map_data':map_data,
            'indv_counts':all_registered_indv_ids.count(),
            'ordering_indv_counts':ordering_indv_counts
        }
    return return_context

def plot_fpos_on_map():
    return ''

def plot_business_on_map():
    return ''

def plot_overseas_on_map():
    return ''


def fuzzy_search(query, items, threshold=70):
    query = query.lower()
    results = []
    for item in items:
        item_lower = item.lower()
        distance = levenshtein_distance(query, item_lower)
        max_len = max(len(query), len(item_lower))
        similarity = ((max_len - distance) / max_len) * 100
        if similarity >= threshold:
            results.append(item)
    if len(results) == 0 and threshold > 50:
        return fuzzy_search(query, items, 50)  # ✅ return recursive result
    return results

def levenshtein_distance(a, b):
    # Create a matrix with size (len(b)+1) x (len(a)+1)
    matrix = [[0] * (len(a) + 1) for _ in range(len(b) + 1)]

    # Initialize first column and first row
    for i in range(len(b) + 1):
        matrix[i][0] = i
    for j in range(len(a) + 1):
        matrix[0][j] = j

    # Fill the matrix
    for i in range(1, len(b) + 1):
        for j in range(1, len(a) + 1):
            cost = 0 if b[i - 1] == a[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,      # Deletion
                matrix[i][j - 1] + 1,      # Insertion
                matrix[i - 1][j - 1] + cost  # Substitution
            )

    return matrix[len(b)][len(a)]


def admin_master(request):
    if request.user.is_authenticated:
        item_qs = Item.objects.values('itemCat').annotate(count=Count('itemID')).order_by('-count')
        customer_qs = CustomUser.objects.values('userType').exclude(userType=0).annotate(count=Count('id')).order_by('-count')
        list_usertype_reverse_dict = {k: v for k, v in LIST_USERTYPES}
        #charts
        item_labels = [entry['itemCat'] for entry in item_qs]
        item_counts = [entry['count'] for entry in item_qs]
        cust_type_code= [entry['userType'] for entry in customer_qs]
        cust_counts = [entry['count'] for entry in customer_qs]
        cust_labels = []
        for code in cust_type_code:
            usertype_value = list_usertype_reverse_dict.get(code)
            cust_labels.append(usertype_value)
        #end of charts
        total_users = CustomUser.objects.all()
        no_of_users = CustomUser.objects.all().__len__() - 1
        no_of_fpo = CustomUser.objects.filter(userType=1).__len__()
        no_of_biz = CustomUser.objects.filter(userType=2).__len__()
        no_of_inst = CustomUser.objects.filter(userType=3).__len__()
        no_of_overseas = CustomUser.objects.filter(userType=4).__len__()
        no_of_indv = CustomUser.objects.filter(userType=5).__len__()
        no_of_items = Item.objects.all().__len__()
        no_of_item_cat = Item.objects.values('itemCat').distinct().count()
        no_of_orders = Order.objects.all().__len__()
        no_of_bulkbuys = BulkBuy.objects.all().__len__()
        enquiries = UserMessage.objects.all()
        
        master_console_context = {
            'total_users':total_users,
            'total_users_no':no_of_users,
            'total_fpo':no_of_fpo,
            'total_business':no_of_biz,
            'total_institutions':no_of_inst,
            'total_overseas':no_of_overseas,
            'total_individual':no_of_indv,
            'no_of_items':no_of_items,
            'no_of_item_cat':no_of_item_cat,
            'total_orders':no_of_orders,
            'total_bulkbuys':no_of_bulkbuys,
            'enquiries':enquiries,
            'item_labels': json.dumps(item_labels),
            'item_counts': json.dumps(item_counts),
            'cust_labels':json.dumps(cust_labels),
            'cust_counts':json.dumps(cust_counts)
        }
        return render(request, 'admin-master-console.html', context=master_console_context)
    else:
        return redirect('login')
#endregion


#region Items
ITEM_TAXPREF = [
    ('1','Taxable'),
    ('2','Non-Taxable'),
    ('3','Out-of-scope'),
    ('4','Non-GST supply')
]
ITEM_TAXRATE = [
    ('1',0),
    ('2',5),
    ('3',12),
    ('4',18),
    ('5',28)
]
ITEM_TYPE = [
    ('1','Goods'),
    ('2','Services'),
]
@login_required
def item_import(request):
    if request.method == 'POST' and request.user.is_authenticated:
        item_type_dict = {v: k for k, v in ITEM_TYPE} #dict(ITEM_TYPE)
        item_taxrate_dict = {v: k for k, v in ITEM_TAXRATE}#dict(ITEM_TAXRATE)
        item_taxpref_dict = {v: k for k, v in ITEM_TAXPREF}#dict(ITEM_TAXPREF)
        excel_form = ItemImportExcelForm(request.POST, request.FILES)
        if excel_form.is_valid():
            excel_file = request.FILES['excel_file']
            try:
                df = pd.read_excel(excel_file)
                for _, row in df.iterrows():
                    x = row['itemType']
                    y = row['itemTaxRate']
                    z = row['itemTaxPref']
                    item_type = item_type_dict.get(x)
                    item_taxrate = item_taxrate_dict.get(y)
                    item_taxpref = item_taxpref_dict.get(z)
                    Item.objects.create(
                        itemType=item_type,
                        itemName=row['itemName'],
                        itemCat=row['itemCat'],
                        itemSku=row['itemSku'],
                        itemHSNCode=row['itemHSNCode'],
                        itemUnit=row['itemUnit'],
                        itemTaxPref=item_taxpref,
                        itemTaxRate=item_taxrate,
                        itemCostPrice=row['itemCostPrice'],
                        itemPrice=row['itemPrice'],
                        stockValue=row['stockValue'],
                        itemImg=row['itemImg'],
                        itemActive = True,
                        itemInStock = True,
                        marketType='All',
                        featureItem = True,
                        itemDesc = row['itemDesc'],
                        userID_id = request.user.pk
                    )
                return redirect('item_list')
            except Exception as e:
                print(e)
                messages.error(request,f'Error occured while importing the file!{e}')
                return redirect('item_list')
            else:
                excel_form = ItemImportExcelForm
    return redirect('item_list')

@login_required
def item_entry(request):
    itemform = ItemForm()
    user_name = request.user.last_name
    return render(request, 'item_entry.html', {'form':itemform, 'login_user':user_name})
    #return render(request, 'admin-console.html', {'form':itemform, 'login_user':user_name})

@login_required
def create_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        itemStock = request.POST['stockValue']
        if form.is_valid():
            usertype = request.user.userType
            if usertype == '1':#usertype 1 means it is an FPC
                form.save(userid=request.user.pk)
                item_ID = Item.objects.all().latest('itemID').itemID
                stockEntry = ItemStock(itemID_id=item_ID,stockValue=itemStock)
                stockEntry.save()
                return redirect('item_list')#JsonResponse({'success': True})
                #return redirect('admin-console')#JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False})

@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, itemID=item_id)
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save(userid=request.user.pk)
            messages.success(request, 'Item updated successfully.')
            return redirect('item_list')
            # return redirect('admin-console')#JsonResponse({'success': True})
        else:
            msg = form.errors.as_data()
    else:
        form = ItemForm(instance=item)
    user_name = request.user.last_name
    return render(request, 'item_entry.html', {'form': form, 'is_edit': True, 'login_user':user_name})

@login_required
def change_item_status(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if item.itemActive == False:
        Item.objects.filter(itemID=item_id).update(itemActive=True)
        pass
    else:
        Item.objects.filter(itemID=item_id).update(itemActive=False)
        pass
    return redirect('item_list')
    # return redirect('admin-console')

@login_required
def item_stockout(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if item.itemInStock == False:
        Item.objects.filter(itemID=item_id).update(itemInStock=True)
        pass
    else:
        Item.objects.filter(itemID=item_id).update(itemInStock=False)
        pass
    return redirect('item_list')
    # return redirect('admin-console')

@login_required
def item_feature(request,item_id):
    item = get_object_or_404(Item, pk=item_id)
    if item.featureItem == False:
        Item.objects.filter(itemID=item_id).update(featureItem=True)
        pass
    else:
        Item.objects.filter(itemID=item_id).update(featureItem=False)
        pass
    return redirect('item_list')
    # return redirect('admin-console')

def item_list(request):
    login_user_id = request.user.pk
    if request.user.is_authenticated:
        user_name = request.user.last_name
        user_approved=request.user.userApproved
        """if the user is not an FPO then the page should not be displayed"""
        if request.user.userType != '1':
            return redirect('index')
    else:
        user_name = 'Guest!'
        user_approved=''
    if login_user_id is not None:
        items = Item.objects.filter(userID_id = login_user_id)
    else:
        items = Item.objects.all()
    form = ItemForm()
    excel_form = ItemImportExcelForm()

    total_items = Item.objects.filter(userID_id=request.user.pk)#total items placed by the vendor/FPO
    total_featured_items = Item.objects.filter(userID_id=request.user.pk, featureItem=True).__len__()#featured items as set by the FPO
    total_item_categories = Item.objects.filter(userID_id=request.user.pk).values('itemCat').distinct().__len__()#distinct categories of items stored by the FPO
    total_instock_items = Item.objects.filter(userID_id=request.user.pk, itemInStock=True).__len__()#total in stock of items stored by the FPO
    total_active_items = Item.objects.filter(userID_id=request.user.pk, itemActive=True).__len__()#distinct categories of items stored by the FPO
    item_list_context = {
        'items': items, 
        'form': form,
        'excel_form':excel_form, 
        'login_user':user_name,
        'user_approved':user_approved,
        'total_items':total_items,
        'total_featured_items':total_featured_items,
        'total_item_categories':total_item_categories,
        'total_instock_items':total_instock_items,
        'total_active_items':total_active_items
    }
    return render(request, 'item_list.html', context=item_list_context)

# def pincode_item_list(request, pincode):
#     query = f'SELECT A.* FROM omsapp_item AS A INNER JOIN omsapp_customuser AS B ON A.userID_id=B.id AND B.userType=1 AND B.pinCode={pincode};'
#     with connection.cursor as cursor:
#         cursor.execute(query)
#         pincode_items = cursor.fetchall()
#     user_name = request.user.last_name
#     item_context = {'items':pincode_items, 'login_user':user_name}
#     return JsonResponse(item_context)
#endregion

#region cart management with session id (without login and with login)
def add_to_cart(request, product_id):
    """check whether the product belongs to self"""
    userID = request.user.pk
    product_owner = get_object_or_404(Item, itemID=product_id).userID.pk
    if userID == product_owner:
        return redirect('shop')
    source = request.GET.get('source')
    qty = request.GET.get('qty')
    selectedQty = qty
    cart = Cart(request)
    product = get_object_or_404(Item, itemID=product_id)
    if selectedQty is None or selectedQty == '':
        selectedQty = request.POST['quantity']
    qty = int(selectedQty)
    cart.add(product=product, quantity=qty, update_quantity=False)
    if source == 'landing':
        return redirect('index')
    elif source == 'shop':
        return redirect('shop')

def update_cart(request):
    cart = Cart(request)
    product_id = request.GET['item']
    selectedQty = request.POST['quantity']
    # data = json.loads(request.body)
    # product_id = data.get('item_id')
    # selectedQty = data.get('quantity')
    product = get_object_or_404(Item, itemID=product_id)
    qty = int(selectedQty)
    cart.add(product=product, quantity=qty, update_quantity=True)
    return redirect('cart')

def remove_from_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Item, itemID=product_id)
    cart.remove(product)
    return redirect('cart')

def cart_view(request):
    cart = Cart(request)
    cart_items = cart.__iter__()
    item_stock = True
    item_seller = False
    for cart_item in cart_items:
        stock = cart_item['product'].itemInStock
        user_id_item = cart_item['product'].userID_id
        if stock == False:
            item_stock = False
        elif user_id_item == request.user.pk:
            item_seller = True
            break
    total_cart_qty = cart.__len__()
    no_of_cart_item = cart.cart.__len__()
    total_cart_price = cart.get_total_price()
    transportation_cost = 0 if total_cart_price > 999 else 99
    grand_total = total_cart_price + transportation_cost
    ds = DeliverySchedule()
    user_name = 'Guest!'#display the username
    pincode='Pincode'
    user_type=''
    user_approved=''
    billing_addresses = None
    shipping_addresses = None
    if request.user.is_authenticated:
        user_name = request.user.last_name
        user_type=request.user.userType
        user_approved = request.user.userApproved
        pincode = request.session.get('pincode')
        billing_addresses = UserBillingAddresses.objects.filter(userID_id=request.user.pk)
        shipping_addresses = UserShippingAddresses.objects.filter(userID_id=request.user.pk)
    shopping_cart_context = {
        'user_type':user_type,
        'user_approved':user_approved,
        'cart': cart, 
        'no_of_cart_item':no_of_cart_item,
        'total_cart_qty':total_cart_qty, 
        'total_cart_price':total_cart_price, 
        'transportation_cost':transportation_cost,
        'gst_amount':0,
        'deduction_amount':0,
        'grand_total':grand_total,
        'dateSeries':ds.dateSeries, 
        'timeSeries':ds.timeSeries, 
        'login_user':user_name,
        'pincode':pincode,
        'billing_addresses':billing_addresses,
        'shipping_addresses':shipping_addresses,
        'add_address_from':'cart',
        'states':LIST_STATES,
        'item_stock':item_stock,
        'item_seller':item_seller
    }
    return render(request, 'cart.html', context=shopping_cart_context)
#endregion

#region Order Mechanism
#region Create Order No. and Invoice No.
def create_order_invoice(param_order_no, param_invoice_no, param_user_id):
    user_id = param_user_id
    date_string = datetime.now().strftime('%y%m%d')
    order_no_string = str(param_order_no)
    invoice_no_string = str(param_invoice_no)
    order_no_len = len(order_no_string)
    invoice_no_leng = len(invoice_no_string)
    def order_no_length(str_len, str_to_add):
        switcher = {
            1: '000'+str_to_add,
            2: '00'+str_to_add,
            3: '0'+str_to_add
        }
        return switcher.get(str_len,'0000')
    order_no = date_string+order_no_length(order_no_len,order_no_string)
    invoice_no = date_string+order_no_length(invoice_no_leng, invoice_no_string)
    return_context = {'orderNo':order_no, 'invoiceNo':invoice_no}
    return return_context
#endregion

#region create order and save order details
@login_required
def CreateOrder(request, param_transportation_cost, param_total_price, param_gst_amount, param_deduction):
    if request.user.is_authenticated:
        if request.method == 'POST' and request.user.is_authenticated:
            paymentMode = request.POST['paymentMode']
            request.session['transportation_cost']=param_transportation_cost
            request.session['total_price']=param_total_price
            request.session['gst_amount']=param_gst_amount
            request.session['deduction']=param_deduction
            request.session['delivery_date']=request.POST['selectDeliveryDate']
            request.session['deliery_time']=request.POST['selectDeliveryTime']
            request.session['order_note'] = request.POST['orderNote']
            request.session['pay_method'] = request.POST['paymentMode']
            request.session['pay_status'] = False
            request.session['pay_date'] = None
            request.session['pay_ref'] = None
            if paymentMode == '1':
                create_order(request, param_transportation_cost, param_total_price, param_gst_amount, param_deduction)
            elif paymentMode == '2':
                create_order(request, param_transportation_cost, param_total_price, param_gst_amount, param_deduction)
            elif paymentMode == '3':
                return redirect('initiate_payment')

            clear_session_variables(request)
            return redirect(f"{reverse('order_successful')}?success={'Order'}")
        else:
            pay_type = request.GET['pay']
            if pay_type == 'online':
                param_transportation_cost = request.session['transportation_cost']
                param_total_price = request.session['total_price']
                param_gst_amount = request.session['gst_amount']
                param_deduction = request.session['deduction']
                request.session['pay_status'] = True
                request.session['pay_date'] = timezone.now()
                request.session['pay_ref'] = 'ONL'+str(int(timezone.now().timestamp() * 1000))#this will be updated with razorpay reference number
                create_order(request, param_transportation_cost, param_total_price, param_gst_amount, param_deduction)
                clear_session_variables(request)
                return redirect(f"{reverse('order_successful')}?success={'Order'}")
            else:
                return render('shoppingcart')
    else:
        return redirect('login')

def clear_session_variables(request):
    del request.session['transportation_cost']
    del request.session['total_price']
    del request.session['gst_amount']
    del request.session['deduction']
    del request.session['delivery_date']
    del request.session['deliery_time']
    del request.session['order_note']
    del request.session['pay_method']
    del request.session['pay_status']
    del request.session['pay_date']
    del request.session['pay_ref']
    return True

def create_order(request, param_transportation_cost, param_total_price, param_gst_amount, param_deduction):
    form = OrderForm(request.POST)
    if form.is_valid():
        userdetails = get_object_or_404(CustomUser, id = request.user.id)
        user_id = userdetails
        fetched_invoice_no = 0
        with connection.cursor() as cursor:
            cursor.execute("SELECT seq FROM sqlite_sequence WHERE name = %s", ['omsapp_order'])
            row = cursor.fetchone()
            if row:
                fetched_order_id = row[0]
            else:
                fetched_order_id = 1

        dict_order_invoice = create_order_invoice(fetched_order_id, fetched_invoice_no, user_id)
        view_orderNo = dict_order_invoice['orderNo']+'N'
        view_orderDate = datetime.now()
        view_orderStatus = 'Pending Order'
        view_orderAmount = param_total_price
        view_orderGSTAmount = param_gst_amount
        view_orderDeduction = param_deduction
        view_transportationCost = param_transportation_cost
        view_orderGrandTotal = float(view_orderAmount)+float(view_orderGSTAmount)-float(view_orderDeduction)+float(view_transportationCost)
        view_orderDeliveryDate = request.session.get('delivery_date')
        view_orderDeliveryTime = request.session.get('deliery_time')
        view_orderNote = request.session.get('order_note')
        view_pay_method = request.session.get('pay_method')
        view_pay_status = request.session.get('pay_status')
        view_pay_date = request.session.get('pay_date')
        view_pay_ref = request.session.get('pay_ref')
        order_context = Order(orderNo= view_orderNo,
                        orderDate=view_orderDate, 
                        orderStatus=view_orderStatus,
                        orderAmount=view_orderAmount,
                        orderGSTAmount=view_orderGSTAmount,
                        orderDeduction=view_orderDeduction,
                        orderTransportation = view_transportationCost,
                        orderGrandTotal=view_orderGrandTotal,
                        schDeliveryDate = view_orderDeliveryDate,
                        schDeliveryTime = view_orderDeliveryTime,
                        orderNote = view_orderNote,
                        paymentMode = view_pay_method,
                        paymentStatus = view_pay_status,
                        paymentDate = view_pay_date,
                        paymentRefNo = view_pay_ref,
                        userID_id=request.user.pk)
        try:
            order_context.save()
            order_id = Order.objects.all().latest('orderID').orderID
            if SaveOrderDetails(request, order_id, user_id) == True:
                if view_pay_method == '3':
                    return view_orderNo
                    return redirect(f"{reverse('order_successful')}?success={'Order'}")
                else:
                    return redirect(f"{reverse('order_successful')}?success={'Order'}")
                #return render(request,'success.html',success_context)#HttpResponse('<h2>Order Placed Successfully!</h2>')
            else:
                return render(request,'404.html',{'source':'Order'})
        except Exception as ex:
            return render(request,'404.html',{'source':'Order'})
    else:
        return render(request,'404.html',{'source':'Invalid Form'})

def SaveOrderDetails(request,param_orderID,param_user_id):
    #if request.method == 'POST':
        #cart_id = Cart.objects.filter(user_id=param_user_id)[0]
    cart_items =  Cart(request) #CartItem.objects.filter(cart_id=cart_id)
    try:
        vendor_ids = []
        suborderID=0
        for eachitem in cart_items:
            if [param_orderID, eachitem['product'].userID_id, param_user_id.pk] not in vendor_ids:
                vendor_ids.append([param_orderID, eachitem['product'].userID_id, param_user_id.pk])
                SubOrder.objects.create(
                    orderID_id = param_orderID,
                    vendorID_id = eachitem['product'].userID_id,
                    customerID_id = param_user_id.pk,
                    orderNote = request.session.get('order_note'),#request.POST['orderNote'],
                    paymentMode= request.session.get('pay_method'),#request.POST['selectPaymentMethod']
                    paymentStatus = request.session.get('pay_status'),
                    paymentDate = request.session.get('pay_date'),
                    paymentRefNo = request.session.get('pay_ref')
                )
                suborderID = SubOrder.objects.all().latest('suborderID').suborderID
            else:
                suborderID = SubOrder.objects.get(orderID_id = param_orderID, vendorID_id = eachitem['product'].userID_id, customerID_id=param_user_id.pk).suborderID
            OrderDetails.objects.create(
                suborderID_id = suborderID,
                orderID_id = param_orderID,
                itemID_id = eachitem['product'].itemID,
                itemQty = eachitem['quantity'],
                itemPrice = eachitem['price'],
                itemGST = 0,
                itemGSTAmount = 0,
                itemPricewithGST = eachitem['total_price'],
            )
            cart_items.remove(eachitem['product'])
            del eachitem
        return True
    except Exception as ex:
        print(ex)
        return False
        #print(ex)

def order_successful(request):
    type = request.GET.get('success')
    pay_ref=request.GET.get('payref')
    user_name = request.user.last_name
    pincode = request.session.get('pincode')
    if type == 'Bulk':
        orderID = BulkBuy.objects.all().latest('bulkBuyID').bulkBuyID
        orderNo = BulkBuy.objects.all().latest('bulkBuyID').bulkBuyNo
    elif type == 'Order':
        orderID = Order.objects.all().latest('orderID').orderID
        orderNo = Order.objects.all().latest('orderID').orderNo
    else:
        orderID = ''
        orderNo = ''

    success_context = {
        'orderID': orderID,
        'orderNo': orderNo,
        'login_user': user_name,
        'pincode':pincode,
        'orderType':type,
        'pay_ref':pay_ref
    }
    return render(request,'success.html',success_context)
#endregion

#region billing page
def billing(request):
    return render(request,'billing.html',{})
#endregion

#endregion

#region Received Orders
@login_required
def ReceivedOrders(request):    
    if request.user.pk is not None:
        #received_orders = Order.objects.all()
        user_name = request.user.last_name
        received_orders = SubOrder.objects.filter(vendorID_id=request.user.pk).__len__()#total orders received by the FPO
        pending_orders = SubOrder.objects.filter(orderStatus = 'Pending Order', vendorID_id=request.user.pk).__len__()
        invoiced_orders = SubOrder.objects.filter(orderStatus = 'Invoiced', vendorID_id=request.user.pk).__len__()
        delivered_orders = SubOrder.objects.filter(orderStatus = 'Delivered',vendorID_id=request.user.pk).__len__()
        rejected_orders = SubOrder.objects.filter(orderStatus = 'Rejected', vendorID_id=request.user.pk).__len__()
        orders = SubOrder.objects.filter(vendorID_id=request.user.pk).order_by('-suborderID')
        context = {
            'received_sub_orders': received_orders, 
            'orders':orders,
            'pending_orders':pending_orders,
            'invoiced_orders':invoiced_orders,
            'delivered_orders':delivered_orders,
            'rejected_orders':rejected_orders,
            'login_user':user_name
        }
        
        return render(request, 'orders_received.html', context=context)
    else:
        return render(request, 'orders_received.html', {})

LIST_PAYMENT_MODES = [
    ('Cash on Delivery', 1),
    ('Institutional Credit', 2),
    ('Online', 3)
]

def received_orders_details(request, orderID):
    if request.user.pk is not None:
        orderNo = Order.objects.get(pk=orderID).orderNo
        orderFrom = Order.objects.get(pk=orderID).userID.last_name
        userID = Order.objects.get(pk=orderID).userID.pk
        shipping_address = UserShippingAddresses.objects.annotate(
            address = Concat(
                'userAddress1', Value(','),
                'userCity1', Value(','),
                'userState1', Value(','),
                'pinCode1'
            )
        ).get(userID_id=userID, setDefault=True)
        shipping_address.address = f"{shipping_address.userAddress1},{shipping_address.userCity1_name},{shipping_address.userState1_name},{shipping_address.pinCode1}"
        orderNote = Order.objects.get(pk=orderID).orderNote
        payment_mode = Order.objects.get(pk=orderID).paymentMode
        list_reverse_dict = {v: k for k, v in LIST_PAYMENT_MODES}
        payment_mode = list_reverse_dict.get(payment_mode)
        payment_status = 'Paid' if Order.objects.get(pk=orderID).paymentStatus else 'Unpaid'
        payment_date = Order.objects.get(pk=orderID).paymentDate
        payment_ref = Order.objects.get(pk=orderID).paymentRefNo
        suborderID = SubOrder.objects.get(orderID_id=orderID, vendorID_id=request.user.pk).suborderID
        suborder_details = SubOrder.objects.get(orderID_id=orderID, vendorID_id=request.user.pk)
        received_orders = OrderDetails.objects.filter(suborderID_id=suborderID).select_related('itemID')
        existing_invoices = OrderInvoice.objects.filter(orderID_id=orderID,suborderID_id=suborderID)
        user_name = request.user.last_name
        delivery_order = OrderDelivery.objects.filter(orderID_id=orderID, suborderID_id=suborderID) if OrderDelivery.objects.filter(orderID_id=orderID, suborderID_id=suborderID).count() > 0 else 0
        invoiceForm = InvoiceForm()
        context = {
            'received_orders': received_orders,
            'suborder_remark':suborder_details.remark,
            'suborder_status':suborder_details.orderStatus,
            'orderFrom':orderFrom,
            'shipping_address':shipping_address.address,
            'orderNote':orderNote,
            'login_user':user_name, 
            'orderNo':orderNo, 
            'orderID':orderID, 
            'suborderID':suborderID, 
            'invoice':invoiceForm, 
            'existing_invoices':existing_invoices,
            'payment_mode':payment_mode,
            'payment_status':payment_status,
            'payment_date':payment_date,
            'payment_ref':payment_ref,
            'delivery_order':delivery_order
        }
        return render(request, 'rcv_orderdetails.html', context=context)
    else:
        return render(request, 'rcv_orderdetails.html', {})
    
def recived_order_status_update(request, order_details_id):
    if request.user.is_authenticated:
        status = request.resolver_match.url_name
        reject_remark = request.GET.get('reject_remark')
        mainOrderID = get_object_or_404(OrderDetails, id=order_details_id).orderID.pk
        sub_order_id = get_object_or_404(OrderDetails, id=order_details_id).suborderID.pk
        if status == 'acceptorder':
            update_status = OrderDetails.objects.filter(id=order_details_id).update(orderStatus='Accepted', remark='Accepted')
            update_status_of_suborder(sub_order_id)
            pass
        elif status =='rejectorder':
            update_status = OrderDetails.objects.filter(id=order_details_id).update(orderStatus='Rejected', remark='Rejected-'+reject_remark)
            update_status_of_suborder(sub_order_id)
            pass
        if update_status > 0:
            orderUpdate = Order.objects.filter(orderID=mainOrderID).update(orderStatus='Under Process')
            jsonData = {'Success':True}
        else:
            jsonData = {'Success':False}
        return JsonResponse(jsonData)#redirect('receivedorderdetails', orderID=mainOrderID)

def update_status_of_suborder(param_sub_order_id):
    no_of_items_in_suborder = OrderDetails.objects.filter(suborderID_id=param_sub_order_id).count()
    no_of_accepted_items = OrderDetails.objects.filter(suborderID_id=param_sub_order_id, orderStatus='Accepted').count()
    no_of_rejected_items = OrderDetails.objects.filter(suborderID_id=param_sub_order_id, orderStatus='Rejected').count()
    if no_of_items_in_suborder == no_of_accepted_items+no_of_rejected_items:
        suborder_update_status = SubOrder.objects.filter(pk=param_sub_order_id).update(orderStatus='Under Process', remark='Under Process')

def received_order_status_all(request, param_order_id):#the order id is the suborder id
    if request.user.is_authenticated:
        param_sub_order_id = param_order_id
        userid = request.user.pk
        status = request.resolver_match.url_name
        mainOrderID = get_object_or_404(SubOrder, pk=param_sub_order_id).orderID
        if status == 'acceptall':
            item_order_status = OrderDetails.objects.filter(suborderID_id=param_sub_order_id).select_related('itemID').filter(itemID__userID=userid).update(orderStatus='Accepted', remark='Accepted')
            suborder_update_status = SubOrder.objects.filter(pk=param_sub_order_id).update(orderStatus='Under Process', remark='Accepted')
            order_update_status = Order.objects.filter(pk=mainOrderID.pk).update(orderStatus='Under Process', remark='CheckedAll')
            calculate_status_of_all_orders(mainOrderID.pk)
            return JsonResponse({'Success': True})
        elif status == 'rejectall':
            reject_remark = request.GET.get('reject_remark')
            item_order_status = OrderDetails.objects.filter(suborderID_id=param_sub_order_id).select_related('itemID').filter(itemID__userID=userid).update(orderStatus='Rejected', remark='Rejected-'+reject_remark)
            suborder_update_status = SubOrder.objects.filter(pk=param_sub_order_id).update(orderStatus='Rejected', remark='Rejected-'+reject_remark)
            order_update_status = Order.objects.filter(pk=mainOrderID.pk).update(orderStatus='Under Process', remark='CheckedAll')
            calculate_status_of_all_orders(mainOrderID.pk)
            return JsonResponse({'Success':True})
        else:
            return JsonResponse({'Success':False})
    pass

def calculate_status_of_all_orders(orderID):
    #The function checks whether the suborders in the order are accepted all or rejected all and updates the main order accordingly
    no_of_suborders = SubOrder.objects.filter(orderID_id=orderID).count()
    no_of_suborders_rejected = SubOrder.objects.filter(orderID_id=orderID, orderStatus='Rejected').count()
    no_of_suborders_accepted = SubOrder.objects.filter(orderID_id=orderID, orderStatus='Accepted').count()
    if no_of_suborders == no_of_suborders_rejected:
        order_update_status = Order.objects.filter(orderID=orderID).update(orderStatus='Rejected', remark='Rejected')
    elif no_of_suborders == no_of_suborders_accepted:
        order_update_status = Order.objects.filter(orderID=orderID).update(orderStatus='Accepted', remark='Accepted')
    return JsonResponse({'Success':True})

def upload_invoice(request,suborderID):
    if request.method == "POST":
        form = InvoiceForm(request.POST, request.FILES)
        if form.is_valid():
            userid = request.user.pk
            orderID = get_object_or_404(SubOrder,pk=suborderID).orderID.pk
            form.save(userID=userid, orderID=orderID, suborderID=suborderID)
            update_status = SubOrder.objects.filter(pk=suborderID).update(orderStatus='Invoiced', remark='Invoiced')
            no_of_invoices = OrderInvoice.objects.filter(orderID_id=orderID).count()
            no_of_suborders = SubOrder.objects.filter(orderID_id=orderID).count()
            if no_of_invoices == no_of_suborders:
                update_order_status = Order.objects.filter(pk=orderID).update(orderStatus='Invoiced')
            return redirect('receivedorders')  # Redirect to prevent resubmission
    else:
        form = InvoiceForm()
    files = Order.objects.all()
    return render(request, 'rcv_orderdetails.html', {'form': form, 'files': files})

def invoiced_orders(request):
    if request.user.is_authenticated:
        query = f"SELECT DISTINCT orderNo, orderDate, schDeliveryDate, schDeliveryTime, A.orderStatus, first_name, orderID FROM omsapp_order AS A INNER JOIN omsapp_orderdetails AS B ON A.orderID=B.orderID_id AND A.orderStatus='Invoiced' INNER JOIN omsapp_item AS C ON B.itemID_id=C.itemID AND C.userID_id={request.user.id} INNER JOIN omsapp_customuser AS D ON D.id=A.userID_id"
        with connection.cursor() as cursor:
            cursor.execute(query)
            received_orders = cursor.fetchall()
            user_name = request.user.last_name
        context = {'received_orders': received_orders, 'login_user':user_name}
        return render(request, 'orders_invoiced.html', context=context)
    else:
        return render(request, 'orders_invoiced.html', {})
    
def confirm_delivery_order(request, suborder_id):
    if request.user.is_authenticated and request.method == "POST":
        user_name = request.user.last_name
        suborder_delivery = SubOrder.objects.filter(pk=suborder_id).update(orderStatus='Delivered',remark='Delivered')
        main_order_id = get_object_or_404(SubOrder, pk=suborder_id).orderID.pk
        order_deilvery = Order.objects.filter(pk=main_order_id).update(orderStatus='Delivered')    
        #delivery = OrderDelivery.objects.get_or_create(orderID_id=main_order_id, suborderID_id=suborder_id)
        payment_mode = SubOrder.objects.get(pk=suborder_id).paymentMode
        if payment_mode == 1:
            SubOrder.objects.filter(pk=suborder_id).update(paymentStatus=True, paymentDate=timezone.now(),paymentRefNo='COD'+str(int(timezone.now().timestamp() * 1000)))
            Order.objects.filter(pk=main_order_id).update(paymentStatus=True, paymentDate=timezone.now(),paymentRefNo='COD'+str(int(timezone.now().timestamp() * 1000)))
        elif payment_mode == 2:
            SubOrder.objects.filter(pk=suborder_id).update(paymentStatus=True, paymentDate=timezone.now(),paymentRefNo='IC'+str(int(timezone.now().timestamp() * 1000)))
            Order.objects.filter(pk=main_order_id).update(paymentStatus=True, paymentDate=timezone.now(),paymentRefNo='IC'+str(int(timezone.now().timestamp() * 1000)))
        
        img_upload_type = request.GET['mode']
        if img_upload_type == 'browse':
            image = request.FILES.get("browsedPhoto")
            if image:
                suborder = get_object_or_404(SubOrder, pk=suborder_id)

                delivery = OrderDelivery.objects.create(
                    orderID=suborder.orderID,
                    suborderID=suborder,
                    deliveryImg=image,
                    timestamp=timezone.now()
                )
                order_no = get_object_or_404(Order, pk=main_order_id).orderNo
                messages.success(request, "Order is successfully delivered and Image is uploaded! Order #: " + order_no)
                return redirect('receivedorderdetails', orderID=main_order_id)
            else:
                messages.error(request, "No image was uploaded.")
                return redirect('confirmdelivery', suborderID=suborder_id)
        elif img_upload_type == 'click':
            # #image storing procedure
            try:
                # Get uploaded image from FormData
                image_file = request.FILES.get('image')
                if not image_file:
                    return JsonResponse({'status': 'error', 'message': 'No image uploaded'})

                # Get other fields
                latitude = float(request.POST.get('latitude'))
                longitude = float(request.POST.get('longitude'))
                timestamp_str = request.POST.get('timestamp')

                timestamp = parse_datetime(timestamp_str) if timestamp_str else timezone.now()

                suborder = SubOrder.objects.get(pk=suborder_id)

                delivery = OrderDelivery.objects.create(
                    orderID=suborder.orderID,
                    suborderID=suborder,
                    deliveryImg=image_file,
                    latitude=latitude,
                    longitude=longitude,
                    timestamp=timestamp
                )

                return JsonResponse({'status': 'success', 'photo_id': delivery.pk})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        
    return redirect('receivedorders')#redirect to delivered orders

def delivered_orders(request):
    if request.user.is_authenticated:
        query = f"SELECT DISTINCT orderNo, orderDate, schDeliveryDate, schDeliveryTime, A.orderStatus, first_name, orderID FROM omsapp_order AS A INNER JOIN omsapp_orderdetails AS B ON A.orderID=B.orderID_id AND A.orderStatus='Delivered' INNER JOIN omsapp_item AS C ON B.itemID_id=C.itemID AND C.userID_id={request.user.id} INNER JOIN omsapp_customuser AS D ON D.id=A.userID_id"
        with connection.cursor() as cursor:
            cursor.execute(query)
            received_orders = cursor.fetchall()
            user_name = request.user.last_name
        context = {'received_orders': received_orders, 'login_user':user_name}
        return render(request, 'orders_delivered.html', context=context)
    else:
        return render(request, 'orders_delivered.html', {})
    
def pending_orders(request):
     if request.user.is_authenticated:
        query = f"SELECT DISTINCT orderNo, orderDate, schDeliveryDate, schDeliveryTime, A.orderStatus, first_name, orderID FROM omsapp_order AS A INNER JOIN omsapp_orderdetails AS B ON A.orderID=B.orderID_id AND A.orderStatus='Under Process' INNER JOIN omsapp_item AS C ON B.itemID_id=C.itemID AND C.userID_id={request.user.id} INNER JOIN omsapp_customuser AS D ON D.id=A.userID_id"
        with connection.cursor() as cursor:
            cursor.execute(query)
            pending_orders = cursor.fetchall()
            user_name = request.user.last_name
        context = {'pending_orders': pending_orders, 'login_user':user_name}
        return render(request, 'orders_pending.html', context=context)

def rejected_orders(request):
    if request.user.is_authenticated:
        query = f"SELECT DISTINCT orderNo, orderDate, schDeliveryDate, schDeliveryTime, A.orderStatus, first_name, orderID FROM omsapp_order AS A INNER JOIN omsapp_orderdetails AS B ON A.orderID=B.orderID_id AND A.orderStatus='Rejected' INNER JOIN omsapp_item AS C ON B.itemID_id=C.itemID AND C.userID_id={request.user.id} INNER JOIN omsapp_customuser AS D ON D.id=A.userID_id"
        with connection.cursor() as cursor:
            cursor.execute(query)
            rejected_orders = cursor.fetchall()
            user_name = request.user.last_name
        context = {'rejected_orders': rejected_orders, 'login_user':user_name}
        return render(request, 'orders_rejected.html', context=context)

@login_required
def bulk_buy(request):
    if request.user.is_authenticated:
        user_name = request.user.last_name
        userType = USERTYPE_CHOICES(request.user.userType)
        user_type = request.user.userType
        user_approved = request.user.userApproved
        user_address = f"{request.user.userAddress}, {request.user.userCity_name}, {request.user.userState_name}, {request.user.pinCode}"
        user_address1 = user_address#f"{request.user.userAddress1} {request.user.userCity1} {STATE_CHOICES(request.user.userState1)} {request.user.pinCode1}"
        user_phone = request.user.phone
        items = Item.objects.filter(itemActive=True).order_by('-itemInStock').exclude(userID_id=request.user.pk).values('itemName').distinct().order_by('itemName')
        #items = items.exclude(userID_id=request.user.pk)
        distinct_units = items.values('itemUnit').distinct().order_by('itemUnit')
        cart = Cart(request)
        total_cart_qty = cart.__len__()#display total number quantities added in the basket
        total_cart_price = cart.get_total_price()
        pincode = request.session.get('pincode')
    context = {
        'rejected_orders': rejected_orders,
        'clicked':'Bulk',
        'login_user':user_name,
        'user_type':user_type,
        'user_approved':user_approved,
        'userType':userType,
        'user_address':user_address,
        'user_address1':user_address1,
        'user_phone':user_phone,
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price,
        'items':items,
        'distinct_units':distinct_units,
        'pincode':pincode
        }
    return render(request, 'bulk-buy.html', context=context)

@login_required
def bulk_buy_order_place(request):
    if request.user.is_authenticated and request.method == "POST":
        try:
            data = json.loads(request.body)
            delivery_date = data.get('delivery_date')
            user_id = request.user.pk

            with transaction.atomic():
                # Create a temporary BulkBuy object
                bulkBuy = BulkBuy.objects.create(
                    userID_id=user_id,
                    bulkBuyExpDate=delivery_date,
                    bulkBuyNo="TEMP"  # Will be updated after getting ID
                )

                # Generate order number based on the ID
                dict_order_invoice = create_order_invoice(bulkBuy.pk, 0, user_id)
                bulkBuy.bulkBuyNo = dict_order_invoice['orderNo'] + 'B'
                bulkBuy.save()

                for row in data.get("rows", []):
                    BulkBuyDetails.objects.create(
                        bulkBuyID=bulkBuy,
                        itemName=row.get("itemName"),
                        itemSpec=row.get("itemSpec"),
                        itemQty=row.get("itemQty"),
                        itemUnit=row.get("itemUnit"),
                        itemPrice=row.get("itemPrice")
                    )

            return JsonResponse({
                "message": "Bulk buy order placed successfully.",
                "redirect_url": f"{reverse('order_successful')}?success=Bulk"
            })

        except Exception as e:
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Unauthorized or invalid request"}, status=403)

def bulk_buy_order_response(request, bulkBuyID):
    if request.user.is_authenticated:
        user_name = request.user.last_name
        bulkbuyresponses = BulkBuyResponse.objects.annotate(count_enquired_items=Count('bulkBuyID__bulkbuyid_bbd',distinct=True),count_response_items=Count('bulkbuyid_bbrd',distinct=True)).filter(bulkBuyID_id = bulkBuyID)
        cart = Cart(request)
        total_cart_qty = cart.__len__()#display total number quantities added in the basket
        total_cart_price = cart.get_total_price()

    response_context = {
        'bulkbuyresponses':bulkbuyresponses,
        'login_user':user_name,
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price,
    }
    return render(request, 'bulk-buy-order-response.html', context=response_context)

def bulk_buy_order_response_details(request, bulkBuyID, response_userID):
    if request.user.is_authenticated:
        user_name = request.user.last_name
        cart = Cart(request)
        total_cart_qty = cart.__len__()#display total number quantities added in the basket
        total_cart_price = cart.get_total_price()
        order_details = BulkBuyResponse.objects.filter(bulkBuyID_id=bulkBuyID, response_userID_id=response_userID)[0]
        response_remark = BulkBuyResponse.objects.get(bulkBuyID_id=bulkBuyID, response_userID_id=response_userID).response_remark
        if BulkBuyResponse.objects.filter(bulkBuyID_id=bulkBuyID, response_remark='Accepted').__len__() > 0:
            response_accepted = 'Yes'
        else:
            response_accepted = 'No'

        # Filter BulkBuyResponse for matching bulkBuyID and response_userID
        bulkbuy_response_qs = BulkBuyResponse.objects.filter(
            bulkBuyID=bulkBuyID,
            response_userID=response_userID)
        # Prepare Subquery for response details → filter by bbrID (from response) & bbdID (from current detail)
        response_details_qs = BulkBuyResponseDetails.objects.filter(
            bbrID__in=bulkbuy_response_qs,
            bbdID=OuterRef('pk')
        ).values('itemPrice_response')[:response_userID]
        # Main query: fetch BulkBuyDetails + annotate response price
        response_details = BulkBuyDetails.objects.filter(
            bulkBuyID=bulkBuyID
        ).annotate(
            itemPrice_response=Subquery(response_details_qs)
        ).values(
            'itemName', 'itemQty', 'itemUnit', 'itemPrice', 'itemPrice_response'
        )
        for row in response_details:
            row['price_difference'] = (row['itemPrice_response'] or 0) - (row['itemPrice'] or 0)

        response_details_context = {
            'order_details':order_details,
            'response_details':response_details,
            'login_user':user_name,
            'total_cart_qty':total_cart_qty,
            'total_cart_price':total_cart_price,
            'bulkBuyID':bulkBuyID,
            'response_userID':response_userID,
            'response_remark':response_remark,
            'response_accepted':response_accepted
        }
    return render(request, 'bulk-buy-order-response-details.html', context=response_details_context)

def bulk_buy_response_accept(request, bulkBuyID, response_userID):
    BulkBuyResponse.objects.filter(bulkBuyID_id=bulkBuyID, response_userID_id=response_userID).update(response_remark='Accepted',response_remark_date=datetime.today())
    BulkBuyResponse.objects.filter(bulkBuyID_id=bulkBuyID).exclude(response_userID_id=response_userID).update(response_remark='Not Accepted',response_remark_date=datetime.today())
    BulkBuy.objects.filter(pk=bulkBuyID).update(response_accept='True')
    return redirect('order_successful')

def bulk_buy_details(request, bulk_order_id):
    if request.user.is_authenticated:
        user_name = request.user.last_name
        bulkbuy = BulkBuy.objects.filter(bulkBuyID=bulk_order_id)
        bulkbuy_details = BulkBuyDetails.objects.filter(bulkBuyID=bulk_order_id)
        no_of_response_made = BulkBuyResponse.objects.filter(response_userID_id=request.user.pk, bulkBuyID_id=bulk_order_id).__len__()
    bulk_buy_context = {
        'bulkbuy':bulkbuy,
        'bulk_buy_details':bulkbuy_details,
        'login_user':user_name,
        'bulkBuyID':bulk_order_id,
        'user_id':request.user.pk,
        'no_of_response_made':no_of_response_made
    }
    return render(request, 'bulk-buy-details.html', context = bulk_buy_context)

def bulk_buy_order_details(request, bulk_order_id):
    if request.user.is_authenticated:
        bulkbuy_details = BulkBuyDetails.objects.filter(bulkBuyID_id=bulk_order_id).values()
        bb_len = bulkbuy_details.__len__()
        lst = list(bulkbuy_details)
    return JsonResponse({'bulkbuy_details':list(bulkbuy_details)})


def bulk_buy_supply(request):
    if request.user.is_authenticated:
        userApproved = False if request.user.userApproved == None or False else True
        login_user = request.user.last_name
        bulkorder = BulkBuy.objects.annotate(count_items=Count('bulkbuyid_bbd', distinct=True, ), count_response = Count('bulkbuyid_bbr',distinct=True)).order_by('-bulkBuyID')
        no_of_bulk_buy_orders = bulkorder.__len__()
        no_bulk_buy_orders_responded = BulkBuyResponse.objects.filter(response_userID_id=request.user.pk).__len__()
    bulk_context = {
        'bulkorders':bulkorder,
        'login_user':login_user,
        'userApproved':userApproved,
        'no_of_bulk_buy_orders':no_of_bulk_buy_orders,
        'no_bulk_buy_orders_responded':no_bulk_buy_orders_responded,
    }
    return render(request, 'bulk-buy-supply.html', context=bulk_context)
    #return bulk_context
    # return render(request, 'orders_received.html', context=bulk_context)

def bulk_buy_supply_bid(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            data = json.loads(request.body)
            bulkBuyID_id = data.get('bulkBuyID')
            response_userID_id = request.user.pk
            bbrobj = BulkBuyResponse.objects.create(bulkBuyID_id=bulkBuyID_id, response_userID_id=response_userID_id, response_status=True)
            bbrID = bbrobj.pk
            for row in data.get("rows", []):
                bbdID_id = row.get('bbdid')
                bulkBuyID_id =row.get('bulkBuyID')
                ind_qty = row.get('ind_qty')
                res_qty=row.get('res_qty')
                ind_price=row.get('ind_price')
                res_price=row.get('res_price')
                BulkBuyResponseDetails.objects.create(bbrID_id=bbrID, bbdID_id=bbdID_id, itemPrice_indicative=ind_price, itemPrice_response=res_price, itemQty_indicative=ind_qty, itemQty_response=res_qty)
    return JsonResponse({'redirect_url':'/bulk-buy-supply'})

def bulk_buy_orders(request):
    if request.user.is_authenticated:
        #bulk_orders = BulkBuy.objects.filter(userID_id=request.user.pk)
        bulk_orders = BulkBuy.objects.annotate(count_items=Count('bulkbuyid_bbd', distinct=True),count_responses=Count('bulkbuyid_bbr__response_userID_id', distinct=True)).filter(userID_id=request.user.pk).order_by('-bulkBuyID')
        user_name = request.user.last_name
        user_approved = request.user.userApproved
        user_type = request.user.userType
        cart = Cart(request)
        total_cart_qty = cart.__len__()#display total number quantities added in the basket
        total_cart_price = cart.get_total_price()
        bulk_orders_context = {
            'bulk_orders':bulk_orders,
            'login_user':user_name,
            'total_cart_qty':total_cart_qty,
            'total_cart_price':total_cart_price,
            'user_approved':user_approved,
            'user_type':user_type
        }
    return render(request, 'bulk-buy-orders.html', context=bulk_orders_context)

def bulk_buy_response(request):
    user_name=request.user.last_name
    bulkbuyresponse = BulkBuyResponse.objects.annotate(count_enquired_items=Count('bulkBuyID__bulkbuyid_bbd',distinct=True),count_response_items=Count('bulkbuyid_bbrd',distinct=True)).filter(response_userID_id=request.user.pk)
    bulk_context = {
        'bulkbuyresponse':bulkbuyresponse,
        'login_user':user_name
    }
    #return render(request, 'bulk-buy-response.html', context=bulk_context)
    return bulk_context

def bulk_buy_response_details(request, bbr_id):
    user_name=request.user.last_name
    bulkbuyresponsedetails = BulkBuyResponseDetails.objects.filter(bbrID_id=bbr_id)
    response_context = {
        'response_details':bulkbuyresponsedetails
    }
    return render(request, 'bulk-buy-response-details.html', response_context)
#endregion

#region dropdown choices
def USERTYPE_CHOICES(choice):
    if choice == '1': return 'FPO'
    elif choice == '2': return 'Business'
    elif choice == '3': return 'School'
    elif choice == '4': return 'Overseas'
    else: return 'Individual'

def STATE_CHOICES(state):
    if state == '1': return 'Andhra Pradesh'
    elif state == '2': return 'Arunachal Pradesh'
    elif state == '3': return 'Assam'
    elif state == '4': return 'Bihar'
    elif state == '5': return 'Chhattisgarh'
    elif state == '6': return 'Goa'
    elif state == '7': return 'Gujarat'
    elif state == '8': return 'Haryana'
    elif state == '9': return 'Himachal Pradesh'
    elif state == '10': return 'Jharkhand'
    elif state == '11':return 'Karnataka'
    elif state == '12': return 'Kerala'
    elif state == '13': return 'Madhya Pradesh'
    elif state == '14': return 'Maharashtra'
    elif state == '15': return 'Manipur'
    elif state == '16': return 'Meghalaya'
    elif state == '17': return 'Mizoram'
    elif state == '18': return 'Nagaland'
    elif state == '19': return 'Odisha'
    elif state == '20': return 'Punjab'
    elif state == '21': return 'Rajasthan'
    elif state == '22': return 'Sikkim'
    elif state == '23': return 'Tamil Nadu'
    elif state == '24': return 'Telangana'
    elif state == '25': return 'Tripura'
    elif state == '26': return 'Uttar Pradesh'
    elif state == '27': return 'Uttarakhand'
    elif state == '28': return 'West Bengal'
    elif state == '29': return 'Andaman and Nicobar Islands [UT]'
    elif state == '30': return 'Chandigarh [UT]'
    elif state == '31': return 'Dadra and Nagar Haveli and Daman and Diu [UT]'
    elif state == '32': return 'Delhi [UT]'
    elif state == '33': return 'Jammu and Kashmir [UT]'
    elif state == '34': return 'Ladakh [UT]'
    elif state == '35': return 'Lakshadweep [UT]'
    else: return 'Puducherry [UT]'
#endregion

#region Displayiing the already placed orders
@login_required
def PlacedOrders(request):
    if request.user.is_authenticated:
        pincode = request.user.pinCode
        orders = Order.objects.filter(userID=request.user.id).order_by('-orderID')
        user_name = request.user.last_name
        user_type = request.user.userType
        user_approved = request.user.userApproved
        cart = Cart(request)
        total_cart_qty = cart.__len__()#display total number quantities added in the basket
        total_cart_price = cart.get_total_price()
        render_context = {
            'placed_orders':orders,
            'login_user':user_name,
            'total_cart_qty':total_cart_qty,
            'total_cart_price':total_cart_price,
            'pincode':pincode,
            'user_type':user_type,
            'user_approved':user_approved
        }
        return render(request, 'orders.html', context=render_context)
    else:
        return render(request,'orders.html',{})

def placed_order_details(request,orderID):
    orderNote = Order.objects.get(pk=orderID).orderNote
    paymentStatus = Order.objects.get(pk=orderID).paymentStatus
    paymentRefNo = Order.objects.get(pk=orderID).paymentRefNo
    paymentMode = Order.objects.get(pk=orderID).paymentMode
    order_details = OrderDetails.objects.select_related('itemID').filter(orderID_id=orderID)
    invoice_details = OrderInvoice.objects.filter(orderID_id=orderID)
    delivery_order = OrderDelivery.objects.filter(orderID_id=orderID) if OrderDelivery.objects.filter(orderID_id=orderID).count() > 0 else 0
    #query = str(order_details.query)
    pincode='Pincode'
    user_name = 'Guest!'
    if request.user.is_authenticated:
        user_name = request.user.last_name
        pincode = request.user.pinCode
        #order_invoices = order_invoices(request, orderID)
    cart = Cart(request)
    total_cart_qty = cart.__len__()#display total number quantities added in the basket
    total_cart_price = cart.get_total_price()
    render_context = {
        'order_details':order_details,
        'login_user':user_name,
        'invoices':invoice_details,
        'delivery':delivery_order,
        'total_cart_qty':total_cart_qty,
        'total_cart_price':total_cart_price,
        'pincode':pincode,
        'orderNote':orderNote,
        'paymentStatus':paymentStatus,
        'paymentRefNo':paymentRefNo,
        'paymentMode':paymentMode
    }
    return render(request, 'orderdetails.html', context=render_context)

def order_invoices(request, order_id):
    pass
#endregion

#region Profile Settings, User Profile
@login_required
def profile(request):
    user_name = request.user.last_name
    user_id = request.user.id
    userType = request.user.userType
    profile_context = {'login_user':user_name, 'login_user_id':user_id}
    profile_page = 'profile.html'
    # if userType == '1':
    #     #profile_page = 'dashboard.html'
    #     return redirect('dashboard')
    #     pass
    # else:
    #     return redirect('profileedit')
    return render(request, profile_page, profile_context)

@login_required
def seller_profile(request):
    user_name = request.user.last_name
    userDetails = CustomUser.objects.filter(pk = request.user.pk)
    return render(request, 'seller_profile.html', {'user_details':userDetails, 'login_user':user_name})
#endregion

#region Dashboard
@login_required
def dashboard(request):
    login_user = request.user.last_name
    user_id = request.user.pk
    item_total_revenue = OrderDetails.objects.filter(suborderID__vendorID__id=request.user.pk, orderStatus='Accepted').values('suborderID').aggregate(total_price_with_gst=Sum('itemPricewithGST'))['total_price_with_gst']
    total_items = Item.objects.filter(userID_id=request.user.pk).__len__()#total items placed by the vendor/FPO
    featured_items = Item.objects.filter(userID_id=request.user.pk, featureItem=True).__len__()#featured items as set by the FPO
    total_item_categories = Item.objects.filter(userID_id=request.user.pk).values('itemCat').distinct().__len__()#distinct categories of items stored by the FPO
    total_orders_made = Order.objects.filter(userID_id=request.user.pk).__len__()#total orders placed by the FPO to other entities
    received_orders = SubOrder.objects.filter(vendorID=request.user.pk).__len__()#total orders received by the FPO
    pending_orders = SubOrder.objects.filter(orderStatus = 'Pending Order', vendorID=request.user.pk).__len__()
    invoiced_orders = SubOrder.objects.filter(orderStatus = 'Invoiced').__len__()
    delivered_orders = SubOrder.objects.filter(orderStatus = 'Delivered').__len__()
    rejected_orders = SubOrder.objects.filter(orderStatus = 'Rejected').__len__()
    bulk_buy_orders = BulkBuy.objects.all().__len__()
    bulk_buy_orders_responded = BulkBuyResponse.objects.filter(response_userID_id=user_id).__len__()
    serving_area = FPOServingAddresses.objects.values('userCity1','userCity1_name').filter(userID_id=user_id)
    dashboard_context = {
        'total_revenue': 0 if item_total_revenue == None else item_total_revenue,
        'total_items':total_items,
        'featured_items':featured_items,
        'total_item_categories':total_item_categories,
        'received_orders':received_orders,
        'total_orders_made':total_orders_made,
        'invoiced_orders': invoiced_orders,
        'pending_orders':pending_orders,
        'rejected_orders':rejected_orders,
        'delivered_orders':delivered_orders,
        'bulk_buy':bulk_buy_orders,
        'bulk_buy_response':bulk_buy_orders_responded,
        'serving_area':serving_area
    }
    login_user = request.user.last_name
    return render(request, 'dashboard.html', {'dashboard':dashboard_context, 'login_user':login_user})
#endregion

#region Revenue page
def fpo_revenue(request):
    if request.user.is_authenticated:
        user_name = request.user.last_name
        user_approved=request.user.userApproved
        #"""if the user is not an FPO then the page should not be displayed"""
        if request.user.userType != '1':
            return redirect('index')
    else:
        user_name = 'Guest!'
        user_approved=''

    item_total_revenue = OrderDetails.objects.filter(suborderID__vendorID__id=request.user.pk, orderStatus='Accepted').values('suborderID').aggregate(total_price_with_gst=Sum('itemPricewithGST'))['total_price_with_gst'] or 0
    item_total_revenue_cod = OrderDetails.objects.filter(suborderID__vendorID__id=request.user.pk, orderStatus='Accepted',suborderID__paymentMode=1).values('suborderID').aggregate(total_price_with_gst=Sum('itemPricewithGST'))['total_price_with_gst'] or 0
    item_total_revenue_inc = OrderDetails.objects.filter(suborderID__vendorID__id=request.user.pk, orderStatus='Accepted',suborderID__paymentMode=2).values('suborderID').aggregate(total_price_with_gst=Sum('itemPricewithGST'))['total_price_with_gst'] or 0
    item_total_revenue_onl = OrderDetails.objects.filter(suborderID__vendorID__id=request.user.pk, orderStatus='Accepted',suborderID__paymentMode=3).values('suborderID').aggregate(total_price_with_gst=Sum('itemPricewithGST'))['total_price_with_gst'] or 0
    qs_order_revenue = SubOrder.objects.filter(vendorID_id=request.user.pk).filter(Q(orderStatus='Delivered')|Q(orderStatus='Invoiced'))
    #qs_bulk_revenue = BulkBuyResponse.objects.filter(response_userID_id = request.user.pk)
    rev_context = {
        'item_total_revenue':item_total_revenue,
        'item_total_revenue_cod':item_total_revenue_cod,
        'item_total_revenue_inc':item_total_revenue_inc,
        'item_total_revenue_onl':item_total_revenue_onl,
        'login_user':user_name,
        'user_approved':user_approved,
        'qs_order_revenue':qs_order_revenue,
        #'qs_bulk_revenue':qs_bulk_revenue
    }
    return render(request, 'fpo-revenue.html', context=rev_context)
#endregion

#region FPO Customers
def fpo_customers(request):
    fpo_id = request.user.pk
    qs_so_customers = SubOrder.objects.filter(vendorID_id=fpo_id)
    total_customers = qs_so_customers.values('customerID_id').distinct().count()
    total_schools = qs_so_customers.values('customerID_id').filter(customerID_id__userType='3').distinct().count()
    total_others = total_customers - total_schools
    tab_so_customers = qs_so_customers.filter(orderStatus='Delivered').values('customerID','customerID_id__last_name','customerID_id__userType','customerID_id__phone').annotate(total_orders=Count('suborderID', distinct=True),order_amount=Sum('orderdetails__itemPricewithGST'))
    cust_contxt = {
        'qs_so_customers':qs_so_customers,
        'total_customers':total_customers,
        'total_schools':total_schools,
        'total_others':total_others,
        'tab_so_customers':tab_so_customers
    }
    return render(request, 'fpo-customers.html', context=cust_contxt)
#endregion

#region Payment module (Razorpay integration)
def is_connected(host='api.razorpay.com', port=443, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def initiate_payment(request):
    if is_connected() == True:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        total_price = int(float(request.session['total_price'].strip()))*100 #To convert the amount into paise
        transportation_cost = int(float(request.session['transportation_cost'].strip()))*100
        amount = total_price + transportation_cost
        payment = client.order.create({
            "amount": amount,  # Amount in paise (500.00 INR)
            "currency": "INR",
            "payment_capture": '1'  # auto capture after payment
        })
        context = {
            'payment': payment,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            "label_amount":amount/100
        }
        return render(request, 'checkout.html', context)
    else:
        messages.error(request,'Failed to connect to Internet!')
        return redirect('shoppingcart')

@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        params_dict = {
            'razorpay_order_id': request.POST.get('razorpay_order_id'),
            'razorpay_payment_id': request.POST.get('razorpay_payment_id'),
            'razorpay_signature': request.POST.get('razorpay_signature')
        }

        try:
            client.utility.verify_payment_signature(params_dict)
            # ✅ Payment verified
            total_price = int(float(request.session['total_price'].strip()))
            transportation_cost = int(float(request.session['transportation_cost'].strip()))
            request.session['pay_date']=timezone.now().isoformat()
            request.session['pay_ref']=params_dict['razorpay_payment_id']
            request.session['pay_status']=True
            create_order(request, transportation_cost, total_price, 0, 0)
            return redirect(f"{reverse('order_successful')}?success={'Order'}&payref={params_dict['razorpay_payment_id']}")
        except razorpay.errors.SignatureVerificationError:
            # ❌ Invalid signature
            return HttpResponseBadRequest("Payment verification failed")
    else:
        return HttpResponseBadRequest("Invalid request")

@csrf_exempt  # Allow external POSTs (like Razorpay)
def razorpay_webhook(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    # Step 1: Get Razorpay webhook secret (same as you set in Razorpay dashboard)
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

    # Step 2: Extract payload and signature
    payload = request.body
    received_signature = request.headers.get('X-Razorpay-Signature')

    # Step 3: Verify signature
    expected_signature = hmac.new(
        webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if hmac.compare_digest(received_signature, expected_signature):
        data = json.loads(payload)
        print("✅ Webhook verified and received successfully!")
        print(json.dumps(data, indent=2))  # For dev use, later log/save to DB

        # Optional: Handle specific events like 'payment.captured'
        if data.get('event') == 'payment.captured':
            payment_id = data['payload']['payment']['entity']['id']
            amount = data['payload']['payment']['entity']['amount']
            # Save to DB or mark order as paid here
            print(f"Payment {payment_id} of ₹{amount/100} captured.")

        return JsonResponse({'status': 'Webhook received'})
    else:
        print("❌ Invalid signature.")
        return HttpResponseBadRequest('Invalid signature')
#endregion

#region analytics
def all_analytics_data(userID):
    user_type= get_object_or_404(CustomUser, pk=userID).userType
    if user_type == '1':
        user_all_orders = SubOrder.objects.all().filter(vendorID_id=userID)
        last_name = CustomUser.objects.get(pk=userID).last_name
        no_of_orders = user_all_orders.count()
        no_of_rejected_orders = user_all_orders.filter(orderStatus='Rejected').count()
        no_of_delivered_orders = user_all_orders.filter(orderStatus='Delivered').count()
        no_of_ordered_items = OrderDetails.objects.all().filter(orderID_id__userID_id=userID).count()
        no_of_suppliers = SubOrder.objects.values('customerID_id').filter(orderID_id__userID_id=userID).distinct().count()
        no_of_invoices = OrderInvoice.objects.all().filter(orderID__userID_id=userID).count()
    else:
        user_all_orders = Order.objects.all().filter(userID_id=userID)
        last_name = CustomUser.objects.get(pk=userID).last_name
        no_of_orders = user_all_orders.count()
        no_of_rejected_orders = user_all_orders.filter(orderStatus='Rejected').count()
        no_of_delivered_orders = user_all_orders.filter(orderStatus='Delivered').count()
        no_of_ordered_items = OrderDetails.objects.all().filter(orderID_id__userID_id=userID).count()
        no_of_suppliers = SubOrder.objects.values('vendorID_id').filter(orderID_id__userID_id=userID).distinct().count()
        no_of_invoices = OrderInvoice.objects.all().filter(orderID__userID_id=userID).count()
    analytics_context = {
        'last_name': last_name,
        'userID':userID,
        'order_nos':no_of_orders,
        'no_of_rejected_orders':no_of_rejected_orders,
        'no_of_delivered_orders':no_of_delivered_orders,
        'no_of_ordered_items':no_of_ordered_items,
        'suppliers_nos':no_of_suppliers,
        'no_of_invoices':no_of_invoices
    }
    return analytics_context
def user_analytics(request, userID):
    analytics_context = all_analytics_data(userID)
    ua_context = {
        'last_name': analytics_context['last_name'],
        'userID':analytics_context['userID'],
        'order_nos':analytics_context['order_nos'],
        'no_of_rejected_orders':analytics_context['no_of_rejected_orders'],
        'no_of_delivered_orders':analytics_context['no_of_delivered_orders'],
        'no_of_ordered_items':analytics_context['no_of_ordered_items'],
        'suppliers_nos':analytics_context['suppliers_nos'],
        'no_of_invoices':analytics_context['no_of_invoices']
    }
    return render(request, 'analytics.html', context=ua_context)

def user_analytics_items(request):
    userID = request.GET.get('id')
    analytics_context = all_analytics_data(userID)
    uai_context = {
        'last_name': analytics_context['last_name'],
        'userID':analytics_context['userID'],
        'order_nos':analytics_context['order_nos'],
        'no_of_rejected_orders':analytics_context['no_of_rejected_orders'],
        'no_of_delivered_orders':analytics_context['no_of_delivered_orders'],
        'no_of_ordered_items':analytics_context['no_of_ordered_items'],
        'suppliers_nos':analytics_context['suppliers_nos'],
        'no_of_invoices':analytics_context['no_of_invoices']
    }
    return render(request, 'analytics-items.html', context=uai_context)
#endregion