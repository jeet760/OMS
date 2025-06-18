from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib import messages
from django.db import connection
from django.db.models import Q, Max, Min, Sum, Count, OuterRef, Subquery, F
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.urls import reverse
from datetime import datetime
import json
import requests
import requests.cookies
from .models import CustomUser, UserShippingAddresses, UserBillingAddresses, Login, Item, ItemStock, Order, OrderDetails, Cart, CartItem, OrderInvoice, OrderDelivery, BulkBuy, BulkBuyDetails, BulkBuyResponse, BulkBuyResponseDetails, SubOrder, FPOAuthorisationDocs, UserMessage
from .models import STATES, USERTYPES, GST_TREATMENT
from .forms import ItemForm, UserRegistrationForm, UserLoginForm, OrderForm, OrderDetailsForm, InvoiceForm, FPOAuthrisationForm
from django.contrib.gis.geoip2 import GeoIP2
from .cart import Cart
from .deliveryschedule import DeliverySchedule
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import urlparse



#region StartPage_CommonPages
def landing_page(request, category=None,fpo=None, region=None):
    items = Item.objects.filter(itemActive=True).order_by('-itemInStock')
    query = str(items.query)
    if category is not None:
        items = Item.objects.filter(itemCat=category)
    if fpo is not None:
        items = Item.objects.filter(userID_id=fpo)
    if region is not None:
        regionQuery = f"SELECT A.* FROM omsapp_item A INNER JOIN omsapp_customuser B ON A.userID_id = B.id AND B.userCity='{region}'"
        with connection.cursor() as regionCursor:
            regionCursor.execute(regionQuery)
            items = regionCursor.fetchall()
    
    form = ItemForm()
    user_type = ''
    user_name = 'Guest!'#display the username
    user_approved=''
    pincode = 'Delivery Pincode'
    if request.session.get('pincode') != '' and request.session.get('pincode') != None:
        pincode = request.session.get('pincode')

    featureItems = Item.objects.filter(featureItem=True).exclude(userID_id = request.user.pk)
    if request.user.is_authenticated:
        user_name = request.user.last_name
        user_type = request.user.userType
        user_approved = request.user.userApproved
        if pincode == 'Delivery Pincode':
            pincode = request.user.pinCode1
        request.session['pincode'] = pincode
        if user_type == '1':
            items = items.exclude(userID_id = request.user.pk)
        featureItems = Item.objects.filter(featureItem=True).exclude(userID_id = request.user.pk).filter(userID_id__pinCode=pincode)
    featureItems = featureItems.filter(itemActive=True).order_by('-itemInStock')
    length = items.__len__()#get the total items

    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    region_list = fpo = fpo_list()
    landing_page_context = {
        'items': items, 
        'form': form, 
        'total_items':length, 
        'login_user':user_name,
        'user_type':user_type,
        'user_approved':user_approved, 
        'total_qty':total_qty, 
        'fpo_list':fpo, 
        'regions':region_list,
        'total_price':total_price,
        'featureItems':featureItems,
        'clicked':'Home',
        'pincode':pincode
    }
    return render(request, 'landing.html', landing_page_context)

def shop(request, category=None, fpo=None, region=None):
    items = Item.objects.filter(itemActive=True).order_by('-itemInStock')
    item_sort = request.GET.get('sort')
    user_name = 'Guest!'#display the username
    user_type = ''
    user_approved = ''
    pincode='Delivery Pincode'
    pincode_area = ''
    fpo_name = ''
    if category is not None:
        items = Item.objects.filter(itemCat=category).filter(itemActive=True).order_by('-itemInStock')
    if fpo is not None:
        items = Item.objects.filter(userID_id=fpo).filter(itemActive=True).order_by('-itemInStock')
        fpo_name = get_object_or_404(CustomUser,pk=fpo).last_name
    if region is not None:
        items = Item.objects.filter(userID_id__pinCode=region).filter(itemActive=True).order_by('-itemInStock')
        pincode_area = PinCodeAPI(request, region)
        pincode=region
    form = ItemForm()

    if request.user.is_authenticated:
        user_name = request.user.last_name
        user_type = request.user.userType
        user_approved = request.user.userApproved
        pincode = request.session.get('pincode') #get the logged in user's pincode
        if region is not None: #if the user is logged in and explicitly enters a pincode, then the items of that pincode will be displayed, not the user's own pincode
            pincode = region
            request.session['pincode'] = pincode
        items = Item.objects.filter(userID_id__pinCode=pincode).filter(itemActive=True).order_by('-itemInStock') #if the user is logged in, then only the items available in user's pincode will be available to it.
        if user_type == '1':
            items = items.exclude(userID_id = request.user.pk)
    else:#if the user is not logged in and explicitly enters the pincode
        pincode = region
        request.session['pincode'] = pincode

    if item_sort == 'price_asc':
        items = items.order_by('itemPrice')
    elif item_sort == 'price_desc':
        items = items.order_by('-itemPrice')

    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    region_list = fpo = fpo_list()
    min_price = items.aggregate(Min('itemPrice'))['itemPrice__min']
    max_price = items.aggregate(Max('itemPrice'))['itemPrice__max']
    shop_page_context ={
        'items': items, 
        'form': form, 
        'login_user':user_name,
        'user_approved':user_approved, 
        'total_qty':total_qty, 
        'fpo_list':fpo, 
        'fpo_name':fpo_name,
        'item_sort':item_sort,
        'regions':region_list,
        'total_price':total_price,
        'min_price':min_price,
        'max_price':max_price,
        'pincode_area':pincode_area,
        'clicked':'Shop',
        'pincode':pincode,
        'user_type':user_type
    }
    return render(request, 'shop-grid.html', shop_page_context)

def PinCodeAPI(request, pincode):
    try:
        api_response = requests.get(f'https://api.postalpincode.in/pincode/{pincode}') 
        postalData = api_response.json()
        postoffice_data = postalData[0]['PostOffice']
        return postoffice_data[0]['Name']+", "+postoffice_data[0]['Block']
    except:
        messages.success(request, 'There has been a connetion failure!')
        return HttpResponse({})

def shop_details(request, item_id):
    item = get_object_or_404(Item,pk=item_id)
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    if request.user.is_authenticated:
        user_name=request.user.last_name
        pincode = request.session.get('pincode') #get the logged in user's pincode
        related_items = Item.objects.filter(itemCat = item.itemCat).filter(userID_id__pinCode=pincode)
    else:
        related_items = Item.objects.filter(itemCat = item.itemCat)
    related_items = related_items.exclude(userID_id=request.user.pk)
    user_name = 'Guest!'#display the username
    user_type = ''
    pincode='Delivery Pincode'
    if request.user.is_authenticated:
        user_name=request.user.last_name
        pincode = request.session.get('pincode')
        user_type=request.user.userType
    shop_details_context = {
        'item':item,
        'related_items':related_items,
        'login_user':user_name,
        'user_type':user_type,
        'pincode':pincode,
        'clicked':'Shop',
        'total_qty':total_qty,
        'total_price':total_price
    }
    return render(request, 'shop-details.html', shop_details_context)

def shopping_cart(request):
    cart = Cart(request)
    cart_items = cart.__iter__()
    item_stock = True
    for cart_item in cart_items:
        stock = cart_item['product'].itemInStock
        if stock == False:
            item_stock = False
            break
    total_qty = cart.__len__()
    total_price = cart.get_total_price()
    transportation_cost = 0 if total_price > 999 else 99
    grand_total = total_price + transportation_cost
    ds = DeliverySchedule()
    user_name = 'Guest!'#display the username
    pincode='Delivery Pincode'
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
        'user_authenticated':request.user.is_authenticated, 
        'user_type':user_type,
        'user_approved':user_approved,
        'cart': cart, 
        'total_qty':total_qty, 
        'total_price':total_price, 
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
        'states':STATES,
        'item_stock':item_stock
    }
    return render(request, 'shopping-cart.html', context=shopping_cart_context)

def contact(request):
    qs = request.GET.get('q')
    if request.method == 'POST' and qs == 'msg':
        senderName=request.POST['senderName']
        senderEmail=request.POST['senderEmail']
        senderMsg=request.POST['senderMsg']
        UserMessage.objects.create(name=senderName,email=senderEmail,msg=senderMsg)
        return redirect('contact')
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    user_name = 'Guest!'#display the username
    user_type =''
    user_approved = ''
    pincode='Delivery Pincode'
    pincode = request.session.get('pincode')
    if request.user.is_authenticated:
        user_name = request.user.last_name
        user_type = request.user.userType
        user_approved = request.user.userApproved
    contact_context = {
        'clicked':'Contact',
        'total_qty':total_qty,
        'total_price':total_price,
        'login_user':user_name,
        'pincode':pincode,
        'user_type':user_type,
        'user_approved':user_approved
    }
    return render(request, 'contact.html', contact_context)

def blog(request):
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    blog_context = {
        'clicked':'Blog',
        'total_qty':total_qty,
        'total_price':total_price
    }
    return render(request, 'blog.html', blog_context)

def checkout(request):
    if request.user.is_authenticated:
        checkout_context = {
            'login_user' : request.user.last_name,
            'order_date':datetime.now,
            'order_amount':request.session['total_price']
        }
        return render(request, 'checkout.html', context=checkout_context)
    else:
        return redirect('login')

def fpo_list():
    fpo = CustomUser.objects.filter(userType=1)
    return fpo

def error_404_view(request):
    return render(request, '404.html', {} )

def aboutus(request):
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    aboutus_context = {
        'clicked':'About Us',
        'total_qty':total_qty,
        'total_price':total_price
    }
    return render(request, 'about-us.html', aboutus_context)

def privacypolicy(request):
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    privacy_context = {
        'clicked':'Privacy Policy',
        'total_qty':total_qty,
        'total_price':total_price
    }
    return render(request, 'privacy-policy.html', privacy_context)

def deliverypolicy(request):
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    delivery_context = {
        'clicked':'Delivery Policy',
        'total_qty':total_qty,
        'total_price':total_price
    }
    return render(request, 'delivery-policy.html', delivery_context)

def returnpolicy(request):
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    return_context = {
        'clicked':'Return Policy',
        'total_qty':total_qty,
        'total_price':total_price
    }
    return render(request, 'return-policy.html', return_context)

def eula(request):
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    eula_context = {
        'clicked':'End User',
        'total_qty':total_qty,
        'total_price':total_price
    }
    return render(request, 'eula.html', eula_context)

def testimonials(request):
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    testimonials_context = {
        'clicked':'Testimonials',
        'total_qty':total_qty,
        'total_price':total_price
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
        'states':STATES,
        'gst_tmts': GST_TREATMENT
    }
    return render(request, 'user-form.html', context=user_form_context)

def registration_form(request):
    form = UserRegistrationForm()#new register point: opening the registratino page without login
    user_name = 'Guest!'
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    register_context = {
        'userform': form,
        'login_user':user_name,
        'total_qty':total_qty,
        'total_price':total_price,
        'states':STATES,
        'gst_tmts':GST_TREATMENT,
        'user_types':USERTYPES,
    }
    return render(request, 'register.html', context=register_context)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)#Point: After clicking register button
        if request.user.is_authenticated == False: #update == None:#New registration
            if form.is_valid():
                user = form.save(param_password=request.POST['phone'])
                contact_person = user.last_name
                contact_no = user.phone
                UserBillingAddresses.objects.create(userID_id=user.pk,userAddress=user.userAddress, userCity=user.userCity, userState=user.userState, pinCode=user.pinCode, contactPerson=contact_person, contactNo=contact_no, address_lat=0.00, address_long=0.00, setDefault=True)
                UserShippingAddresses.objects.create(userID_id=user.pk,userAddress1=user.userAddress1, userCity1=user.userCity1, userState1=user.userState1, pinCode1=user.pinCode1, contactPerson1=contact_person, contactNo1=contact_no, address_lat1=0.00, address_long1=0.00, setDefault=True)
                if user.userType != '1':
                    CustomUser.objects.filter(pk=user.id).update(userApproved=True,approvedOn=datetime.today(),isActive=True,activatedOn=datetime.today())
                    login(request, user)
                    user_name = user.last_name
                return redirect('index')  # Redirect to a home page
            else:
                print(form.errors)
                return redirect('index')
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
    contact_person = [CustomUser.objects.get(pk=request.user.pk).contactPerson, CustomUser.objects.get(pk=request.user.pk).contactPerson1, CustomUser.objects.get(pk=request.user.pk).contactNo, CustomUser.objects.get(pk=request.user.pk).contactNo1]
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    register_context = {
        'userform': form,
        'user':user,
        'contact_person':contact_person,
        'login_user':user_name,
        'user_type':user_type,
        'total_qty':total_qty,
        'total_price':total_price,
        'states':STATES,
        'gst_tmts':GST_TREATMENT,
        'user_types':USERTYPES,
        'shipping_addresses':shipping_addresses,
        'billing_addresses':billing_addresses,
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
    CustomUser.objects.filter(pk=userID).update(userApproved=True,approvedOn=datetime.now())
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
    if activate == 'false':
        CustomUser.objects.filter(pk=userID).update(isActive=False,activatedOn=datetime.now())
    else:
        CustomUser.objects.filter(pk=userID).update(isActive=True,activatedOn=datetime.now())
    return redirect('admin-master')

def add_address(request):
    if request.user.is_authenticated:
        userID=request.user.pk
        userAddress = request.POST.get('userAddress')
        userCity = request.POST.get('userCity')
        userState = request.POST.get('userState')
        pinCode = request.POST.get('pinCode')
        contactPerson = request.POST.get('contactPerson')
        contactNo = request.POST.get('contactNo')
        setDefault = True
        type_of_address = request.POST.get('selectAddress')
        if type_of_address == 'bill':
            UserBillingAddresses.objects.filter(userID_id=userID).update(setDefault=False)
            UserBillingAddresses.objects.get_or_create(userID_id=userID, userAddress=userAddress, userCity=userCity,userState=userState,pinCode=pinCode, contactNo=contactNo, contactPerson=contactPerson, address_lat=0.00, address_long=0.00, setDefault=setDefault)
            CustomUser.objects.filter(pk=userID).update(userAddress=userAddress, userCity=userCity,userState=userState,pinCode=pinCode,contactNo=contactNo, contactPerson=contactPerson)
        elif type_of_address == 'ship':
            UserShippingAddresses.objects.filter(userID_id=userID).update(setDefault=False)
            UserShippingAddresses.objects.get_or_create(userID_id=userID, userAddress1=userAddress, userCity1=userCity,userState1=userState,pinCode1=pinCode, contactNo1=contactNo, contactPerson1=contactPerson, address_lat1=0.00, address_long1=0.00, setDefault=setDefault)
            CustomUser.objects.filter(pk=userID).update(userAddress1=userAddress, userCity1=userCity,userState1=userState,pinCode1=pinCode, contactNo1=contactNo, contactPerson1=contactPerson)
        elif type_of_address == 'both':
            UserBillingAddresses.objects.filter(userID_id=userID).update(setDefault=False)
            UserBillingAddresses.objects.get_or_create(userID_id=userID, userAddress=userAddress, userCity=userCity,userState=userState,pinCode=pinCode,contactNo=contactNo, contactPerson=contactPerson, address_lat=0.00, address_long=0.00, setDefault=setDefault)
            UserShippingAddresses.objects.filter(userID_id=userID).update(setDefault=False)
            UserShippingAddresses.objects.get_or_create(userID_id=userID, userAddress1=userAddress, userCity1=userCity,userState1=userState,pinCode1=pinCode, contactNo1=contactNo, contactPerson1=contactPerson, address_lat1=0.00, address_long1=0.00, setDefault=setDefault)
            CustomUser.objects.filter(pk=userID).update(userAddress=userAddress, userCity=userCity,userState=userState,pinCode=pinCode, userAddress1=userAddress, userCity1=userCity,userState1=userState,pinCode1=pinCode)
    
        referer = request.META.get('HTTP_REFERER')
        parsed_url = urlparse(referer)
        path_only = parsed_url.path  # e.g., /some/path/
        if path_only == '/shoppingcart':
            return redirect('shoppingcart')    
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

def fetch_shipping_address(request, id):
    if request.user.is_authenticated:
        q = request.GET.get('q')
        if q == 'bill':
            address = get_object_or_404(UserBillingAddresses, pk=id)
            userID = address.userID.pk
            userAddress = address.userAddress
            userCity=address.userCity
            userState = address.userState
            pinCode = address.pinCode
            contactPerson = address.contactPerson
            contactNo = address.contactNo
        elif q == 'ship':
            address = get_object_or_404(UserShippingAddresses, pk=id)
            userID = address.userID.pk
            userAddress = address.userAddress1
            userCity=address.userCity1
            userState = address.userState1
            pinCode = address.pinCode1
            contactPerson = address.contactPerson1
            contactNo = address.contactNo1

        address_context = {
            'userID':userID,
            'userAddress':userAddress,
            'userCity':userCity,
            'userState':userState,
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
        userCity=request.POST.get('userCity')
        userState = request.POST.get('userState')
        pinCode = request.POST.get('pinCode')
        contactPerson= request.POST.get('contactPerson')
        contactNo = request.POST.get('contactNo')
        CustomUser.objects.filter(pk=userID).update(userAddress=userAddress, userCity=userCity, userState=userState, pinCode=pinCode, contactPerson=contactPerson, contactNo=contactNo)
        UserBillingAddresses.objects.filter(pk=id, userID_id=userID).update(userAddress=userAddress, userCity=userCity, userState=userState, pinCode=pinCode, contactPerson=contactPerson, contactNo=contactNo)
    return redirect('user-form')

def update_shipping_address(request, id):
    if request.user.is_authenticated and request.method == 'POST':
        userID = request.user.pk
        id=request.POST.get('addressID1')
        userAddress = request.POST.get('userAddress1')
        userCity=request.POST.get('userCity1')
        userState = request.POST.get('userState1')
        pinCode = request.POST.get('pinCode1')
        contactPerson= request.POST.get('contactPerson1')
        contactNo = request.POST.get('contactNo1')
        CustomUser.objects.filter(pk=userID).update(userAddress1=userAddress, userCity1=userCity, userState1=userState, pinCode1=pinCode, contactPerson1=contactPerson, contactNo1=contactNo)
        UserShippingAddresses.objects.filter(pk=id, userID_id=userID).update(userAddress1=userAddress, userCity1=userCity, userState1=userState, pinCode1=pinCode, contactPerson1=contactPerson, contactNo1=contactNo)
    return redirect('user-form')

def set_default_address(request, id):
    if request.user.is_authenticated:
        userID = request.user.pk
        type_of_address = request.GET['q']
        if type_of_address == 'bill':
            UserBillingAddresses.objects.filter(userID_id=userID).update(setDefault=False)
            UserBillingAddresses.objects.filter(pk=id, userID_id=userID).update(setDefault=True)
            bill_address = get_object_or_404(UserBillingAddresses, pk=id)
            CustomUser.objects.filter(id=userID).update(userAddress=bill_address.userAddress,userCity=bill_address.userCity,userState=bill_address.userState,pinCode=bill_address.pinCode, bill_address_lat=0.00, bill_address_long=0.00)
        else:
            UserShippingAddresses.objects.filter(userID_id=userID).update(setDefault=False)
            UserShippingAddresses.objects.filter(pk=id, userID_id=userID).update(setDefault=True)
            ship_address = get_object_or_404(UserShippingAddresses, pk=id)
            CustomUser.objects.filter(id=userID).update(userAddress1=ship_address.userAddress1,userCity1=ship_address.userCity1,userState1=ship_address.userState1,pinCode1=ship_address.pinCode1, ship_address_lat=0.00, ship_address_long=0.00)
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
                user = get_object_or_404(CustomUser,username=username)
            except:
                form.add_error(None, 'User does not exist! Please check username and password.')
                messages.success(request, 'User does not exist! Please check username and password.')
                return redirect('login')
            if user.isActive == False:
                form.add_error(None, 'Your Account is not active! Please, contact administrator to activate your account.')
                messages.success(request, 'Your Account is not active! Please, contact administrator to activate your account.')
                return redirect('login')
            if user.userType == '0' and user.is_superuser:
                user_login = authenticate(request, username=username, password=password)
                if user_login is None:
                    form.add_error(None, 'Invalid username or password!')
                    messages.success(request, 'Invalid username or password!')
                    return redirect('login')
                else:
                    login(request, user_login)
                    return redirect('admin-master')
            elif user.userType == '1':
                user_login = authenticate(request, username=username, password=password)
                login(request, user_login)
                return redirect('dashboard')
            else:
                user_login = authenticate(request, username=username, password=password)
                if user_login is not None:
                    login(request, user_login)
                    return redirect('index')
                else:
                    form.add_error(None, 'Invalid username or password!')
                    messages.success(request, 'Invalid username or password!')
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
    return render('admin-master')
def admin_master(request):
    if request.user.is_authenticated:
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
        coordinates = []
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
        }
        return render(request, 'admin-master-console.html', context=master_console_context)
    else:
        return redirect('login')
#endregion


#region Items
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

    total_items = Item.objects.filter(userID_id=request.user.pk)#total items placed by the vendor/FPO
    total_featured_items = Item.objects.filter(userID_id=request.user.pk, featureItem=True).__len__()#featured items as set by the FPO
    total_item_categories = Item.objects.filter(userID_id=request.user.pk).values('itemCat').distinct().__len__()#distinct categories of items stored by the FPO
    total_instock_items = Item.objects.filter(userID_id=request.user.pk, itemInStock=True).__len__()#total in stock of items stored by the FPO
    total_active_items = Item.objects.filter(userID_id=request.user.pk, itemActive=True).__len__()#distinct categories of items stored by the FPO
    item_list_context = {
        'items': items, 
        'form': form, 
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
    cart = Cart(request)
    product = get_object_or_404(Item, itemID=product_id)
    try:
        selectedQty = request.POST['selectQuantity']
    except Exception as ex:
        selectedQty = 1
        #print(ex)
    qty = int(selectedQty)
    cart.add(product=product, quantity=qty, update_quantity=False)
    if source == 'landing':
        return redirect('index')
    elif source == 'shop':
        return redirect('shop')

def update_cart(request):
    cart = Cart(request)
    data = json.loads(request.body)
    product_id = data.get('item_id')
    selectedQty = data.get('quantity')
    product = get_object_or_404(Item, itemID=product_id)
    qty = int(selectedQty)
    cart.add(product=product, quantity=qty, update_quantity=True)
    return redirect('shoppingcart')

def remove_from_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Item, itemID=product_id)
    cart.remove(product)
    return redirect('shoppingcart')

def cart_view(request):
    cart = Cart(request)
    total_qty = cart.__len__()
    total_price = cart.get_total_price()
    ds = DeliverySchedule()
    user_name = 'Guest!'
    if request.user.is_authenticated:
        user_name = request.user.last_name
    
    #return render(request, 'shopping-cart.html', {'cart': cart, 'total_qty':total_qty, 'total_price':total_price, 'user_authenticated':request.user.is_authenticated, 'dateSeries':ds.dateSeries, 'timeSeries':ds.timeSeries, 'login_user':user_name})
    return render(request, 'cart.html', {'cart': cart, 'basket_qty':total_qty, 'basket_price':total_price, 'user_authenticated':request.user.is_authenticated, 'dateSeries':ds.dateSeries, 'timeSeries':ds.timeSeries, 'login_user':user_name})
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
            paymentMode = request.POST['selectPaymentMethod']
            request.session['transportation_cost']=param_transportation_cost
            request.session['total_price']=param_total_price
            request.session['gst_amount']=param_gst_amount
            request.session['deduction']=param_deduction
            request.session['delivery_date']=request.POST['selectDeliveryDate']
            request.session['deliery_time']=request.POST['selectDeliveryTime']
            request.session['order_note'] = request.POST['orderNote']
            request.session['pay_method'] = request.POST['selectPaymentMethod']
            request.session['pay_status'] = False
            request.session['pay_date'] = None
            request.session['pay_ref'] = None
            if paymentMode == '1':
                create_order(request, param_transportation_cost, param_total_price, param_gst_amount, param_deduction)
            elif paymentMode == '2':
                create_order(request, param_transportation_cost, param_total_price, param_gst_amount, param_deduction)
            elif paymentMode == '3':
                return redirect('checkout')

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
    user_name = request.user.last_name
    pincode = request.session.get('pincode')
    if type == 'Bulk':
        orderID = BulkBuy.objects.all().latest('bulkBuyID').bulkBuyID
        orderNo = BulkBuy.objects.all().latest('bulkBuyID').bulkBuyNo
    elif type == 'Order':
        orderID = Order.objects.all().latest('orderID').orderID
        orderNo = Order.objects.all().latest('orderID').orderNo

    success_context = {
        'orderID': orderID,
        'orderNo': orderNo,
        'login_user': user_name,
        'pincode':pincode,
        'orderType':type
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
        orders = SubOrder.objects.filter(vendorID_id=request.user.pk)
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

def received_orders_details(request, orderID):
    if request.user.pk is not None:
        orderNo = Order.objects.get(pk=orderID).orderNo
        orderFrom = Order.objects.get(pk=orderID).userID.last_name
        orderNote = Order.objects.get(pk=orderID).orderNote
        payment_mode = Order.objects.get(pk=orderID).paymentMode
        payment_status = 'Paid' if Order.objects.get(pk=orderID).paymentStatus else 'Unpaid'
        payment_date = Order.objects.get(pk=orderID).paymentDate
        payment_ref = Order.objects.get(pk=orderID).paymentRefNo
        suborderID = SubOrder.objects.get(orderID_id=orderID, vendorID_id=request.user.pk).suborderID
        suborder_details = SubOrder.objects.get(orderID_id=orderID, vendorID_id=request.user.pk)
        received_orders = OrderDetails.objects.filter(suborderID_id=suborderID).select_related('itemID')
        existing_invoices = OrderInvoice.objects.filter(orderID_id=orderID,suborderID_id=suborderID)
        user_name = request.user.last_name
        invoiceForm = InvoiceForm()
        context = {
            'received_orders': received_orders,
            'suborder_remark':suborder_details.remark,
            'suborder_status':suborder_details.orderStatus,
            'orderFrom':orderFrom,
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
            'payment_ref':payment_ref
        }
        return render(request, 'rcv_orderdetails.html', context=context)
    else:
        return render(request, 'rcv_orderdetails.html', {})
    
def recived_order_status_update(request, param_sub_order_id):
    if request.user.is_authenticated:
        status = request.resolver_match.url_name
        reject_remark = request.GET.get('reject_remark')
        mainOrderID = get_object_or_404(OrderDetails, id=param_sub_order_id).orderID.pk
        if status == 'acceptorder':
            update_status = OrderDetails.objects.filter(id=param_sub_order_id).update(orderStatus='Accepted', remark='Accepted'),
            pass
        elif status =='rejectorder':
            update_status = OrderDetails.objects.filter(id=param_sub_order_id).update(orderStatus='Rejected', remark=reject_remark),
            pass
        if update_status[0] > 0:
            orderUpdate = Order.objects.filter(orderID=mainOrderID).update(orderStatus='Under Process')
            jsonData = {'Success':True}
        else:
            jsonData = {'Success':False}
        return JsonResponse(jsonData)#redirect('receivedorderdetails', orderID=mainOrderID)

def received_order_status_all(request, param_order_id):#the order id is the suborder id
    if request.user.is_authenticated:
        userid = request.user.pk
        status = request.resolver_match.url_name
        mainOrderID = get_object_or_404(SubOrder, pk=param_order_id).orderID
        if status == 'acceptall':
            item_order_status = OrderDetails.objects.filter(suborderID=param_order_id).select_related('itemID').filter(itemID__userID=userid).update(orderStatus='Accepted', remark='Accepted')
            suborder_update_status = SubOrder.objects.filter(pk=param_order_id).update(orderStatus='Under Process', remark='Accepted')
            order_update_status = Order.objects.filter(orderID=mainOrderID.pk).update(orderStatus='Under Process', remark='CheckedAll')
            return JsonResponse({'Success': True})
        elif status == 'rejectall':
            reject_remark = request.GET.get('reject_remark')
            item_order_status = OrderDetails.objects.filter(suborderID=param_order_id).select_related('itemID').filter(itemID__userID=userid).update(orderStatus='Rejected', remark=reject_remark)
            suborder_update_status = SubOrder.objects.filter(pk=param_order_id).update(orderStatus='Rejected', remark=reject_remark)
            order_update_status = Order.objects.filter(orderID=mainOrderID.pk).update(orderStatus='Under Process', remark='CheckedAll')
            calculate_rejection_status_of_all_orders(mainOrderID.pk)
            return JsonResponse({'Success':True})
        else:
            return JsonResponse({'Success':False})
    pass

def calculate_rejection_status_of_all_orders(orderID):
    no_of_suborders = SubOrder.objects.filter(orderID_id=orderID).count()
    no_of_suborders_rejected = SubOrder.objects.filter(orderID_id=orderID, orderStatus='Rejected').count()
    if no_of_suborders == no_of_suborders_rejected:
        order_update_status = Order.objects.filter(orderID=orderID).update(orderStatus='Rejected', remark='Rejected')
    return JsonResponse({'Success':True})

def upload_invoice(request,suborderID):
    if request.method == "POST":
        form = InvoiceForm(request.POST, request.FILES)
        if form.is_valid():
            userid = request.user.pk
            orderID = get_object_or_404(SubOrder,pk=suborderID).orderID.pk
            form.save(userID=userid, orderID=orderID, suborderID=suborderID)
            update_status = SubOrder.objects.filter(pk=suborderID).update(orderStatus='Invoiced')
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
    if request.user.is_authenticated:
        user_name = request.user.last_name
        suborder_delivery = SubOrder.objects.filter(pk=suborder_id).update(orderStatus='Delivered',remark='Delivered')
        main_order_id = get_object_or_404(SubOrder, pk=suborder_id).orderID.pk
        order_deilvery = Order.objects.filter(pk=main_order_id).update(orderStatus='Delivered')    
        delivery = OrderDelivery.objects.get_or_create(orderID_id=main_order_id, suborderID_id=suborder_id)
        payment_mode = SubOrder.objects.get(pk=suborder_id).paymentMode
        if payment_mode == 1:
            SubOrder.objects.filter(pk=suborder_id).update(paymentStatus=True, paymentDate=timezone.now(),paymentRefNo='COD'+str(int(timezone.now().timestamp() * 1000)))
            Order.objects.filter(pk=main_order_id).update(paymentStatus=True, paymentDate=timezone.now(),paymentRefNo='COD'+str(int(timezone.now().timestamp() * 1000)))
        elif payment_mode == 2:
            SubOrder.objects.filter(pk=suborder_id).update(paymentStatus=True, paymentDate=timezone.now(),paymentRefNo='IC'+str(int(timezone.now().timestamp() * 1000)))
            Order.objects.filter(pk=main_order_id).update(paymentStatus=True, paymentDate=timezone.now(),paymentRefNo='IC'+str(int(timezone.now().timestamp() * 1000)))
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
        user_address = f"{request.user.userAddress} {request.user.userCity} {STATE_CHOICES(request.user.userState)} {request.user.pinCode}"
        user_address1 = f"{request.user.userAddress1} {request.user.userCity1} {STATE_CHOICES(request.user.userState1)} {request.user.pinCode1}"
        user_phone = request.user.phone
        items = Item.objects.filter(itemActive=True).order_by('-itemInStock').exclude(userID_id=request.user.pk).values('itemName').distinct().order_by('itemName')
        #items = items.exclude(userID_id=request.user.pk)
        distinct_units = items.values('itemUnit').distinct().order_by('itemUnit')
        cart = Cart(request)
        total_qty = cart.__len__()#display total number quantities added in the basket
        total_price = cart.get_total_price()
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
        'total_qty':total_qty,
        'total_price':total_price,
        'items':items,
        'distinct_units':distinct_units,
        'pincode':pincode
        }
    return render(request, 'bulk-buy.html', context=context)

@login_required
def bulk_buy_order_place(request):
    if request.user.is_authenticated:
        #for saving the bulk buy order
        if request.method == "POST":
            user_id = request.user.pk
            data = json.loads(request.body)
            delivery_date = data.get('delivery_date')
            with connection.cursor() as cursor:
                cursor.execute("SELECT seq FROM sqlite_sequence WHERE name = %s", ['omsapp_bulkbuy'])
                row = cursor.fetchone()
                if row:
                    fetched_bulkbuy_id = row[0]
                else:
                    fetched_bulkbuy_id = 1
            dict_order_invoice = create_order_invoice(fetched_bulkbuy_id, 0, user_id)
            bulk_buy_order_no = dict_order_invoice['orderNo']+'B'
            bulkBuyID = BulkBuy.objects.create(userID_id=request.user.pk, bulkBuyExpDate=delivery_date, bulkBuyNo=bulk_buy_order_no)
            for row in data.get("rows", []):
                itemName = row.get("itemName")
                itemSpec = row.get("itemSpec")
                itemQty = row.get("itemQty")
                itemUnit = row.get("itemUnit")
                itemPrice = row.get("itemPrice")
                BulkBuyDetails.objects.create(bulkBuyID=bulkBuyID, itemName=itemName, itemSpec=itemSpec,itemQty=itemQty, itemUnit=itemUnit, itemPrice=itemPrice)
    return redirect(f"{reverse('order_successful')}?success={'Order'}")
    #return redirect('bulk-buy')

def bulk_buy_order_response(request, bulkBuyID):
    if request.user.is_authenticated:
        user_name = request.user.last_name
        bulkbuyresponses = BulkBuyResponse.objects.annotate(count_enquired_items=Count('bulkBuyID__bulkbuyid_bbd',distinct=True),count_response_items=Count('bulkbuyid_bbrd',distinct=True)).filter(bulkBuyID_id = bulkBuyID)
        cart = Cart(request)
        total_qty = cart.__len__()#display total number quantities added in the basket
        total_price = cart.get_total_price()

    response_context = {
        'bulkbuyresponses':bulkbuyresponses,
        'login_user':user_name,
        'total_qty':total_qty,
        'total_price':total_price,
    }
    return render(request, 'bulk-buy-order-response.html', context=response_context)

def bulk_buy_order_response_details(request, bulkBuyID, response_userID):
    if request.user.is_authenticated:
        user_name = request.user.last_name
        cart = Cart(request)
        total_qty = cart.__len__()#display total number quantities added in the basket
        total_price = cart.get_total_price()
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
            'total_qty':total_qty,
            'total_price':total_price,
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
    return redirect('bulk-buy-orders')

def bulk_buy_details(request, bulk_order_id):
    if request.user.is_authenticated:
        user_name = request.user.last_name
        bulkbuy = BulkBuy.objects.filter(bulkBuyID=bulk_order_id)
        bulkbuy_details = BulkBuyDetails.objects.filter(bulkBuyID=bulk_order_id)
        no_of_response_made = BulkBuyResponse.objects.filter(response_userID_id=request.user.pk).__len__()
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
        user_name = request.user.last_name
        bulkorder = BulkBuy.objects.annotate(count_items=Count('bulkbuyid_bbd', distinct=True, ), count_response = Count('bulkbuyid_bbr',distinct=True))
        no_of_bulk_buy_orders = bulkorder.__len__()
        no_bulk_buy_orders_responded = BulkBuyResponse.objects.filter(response_userID_id=request.user.pk).__len__()
    bulk_context = {
        'bulkorders':bulkorder,
        'login_user':user_name,
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
        bulk_orders = BulkBuy.objects.annotate(count_items=Count('bulkbuyid_bbd', distinct=True),count_responses=Count('bulkbuyid_bbr__response_userID_id', distinct=True)).filter(userID_id=request.user.pk)
        user_name = request.user.last_name
        user_approved = request.user.userApproved
        user_type = request.user.userType
        cart = Cart(request)
        total_qty = cart.__len__()#display total number quantities added in the basket
        total_price = cart.get_total_price()
        bulk_orders_context = {
            'bulk_orders':bulk_orders,
            'login_user':user_name,
            'total_qty':total_qty,
            'total_price':total_price,
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
    elif choice == '3': return 'Institution'
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
        pincode = request.user.pinCode1
        orders = Order.objects.filter(userID=request.user.id)
        #invoices = OrderInvoice.objects.select_related('orderID')
        user_name = request.user.last_name
        user_type = request.user.userType
        user_approved = request.user.userApproved
        cart = Cart(request)
        total_qty = cart.__len__()#display total number quantities added in the basket
        total_price = cart.get_total_price()
        render_context = {
            'placed_orders':orders,
            'login_user':user_name,
            'total_qty':total_qty,
            'total_price':total_price,
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
    #query = str(order_details.query)
    pincode='Delivery Pincode'
    user_name = 'Guest!'
    if request.user.is_authenticated:
        user_name = request.user.last_name
        pincode = request.user.pinCode1
        #order_invoices = order_invoices(request, orderID)
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    render_context = {
        'order_details':order_details,
        'login_user':user_name,
        'invoices':invoice_details,
        'total_qty':total_qty,
        'total_price':total_price,
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
    user_name = request.user.last_name
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
        'bulk_buy_response':bulk_buy_orders_responded
    }
    return render(request, 'dashboard.html', {'dashboard':dashboard_context, 'login_user':user_name})
#endregion

#region Payment module (Razorpay integration)
def initiate_payment(request):
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    payment = client.order.create({
        "amount": 50000,  # Amount in paise (500.00 INR)
        "currency": "INR",
        "payment_capture": '1'  # auto capture after payment
    })

    context = {
        'payment': payment,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID
    }
    return render(request, 'payment.html', context)

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
            return render(request, 'success.html', {'payment_id': params_dict['razorpay_payment_id']})
        except razorpay.errors.SignatureVerificationError:
            # ❌ Invalid signature
            return HttpResponseBadRequest("Payment verification failed")
    else:
        return HttpResponseBadRequest("Invalid request")
#endregion