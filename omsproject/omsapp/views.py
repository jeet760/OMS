from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib import messages
from django.db import connection
from django.db.models import Q, Max, Min, Sum, Count, OuterRef, Subquery, F
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from datetime import datetime
import json
import requests
import requests.cookies
from .models import CustomUser, UserAddresses, Login, Item, ItemStock, Order, OrderDetails, Cart, CartItem, Invoice, BulkBuy, BulkBuyDetails, BulkBuyResponse, BulkBuyResponseDetails, SubOrder
from .models import STATES, USERTYPES, GST_TREATMENT
from .forms import ItemForm, UserRegistrationForm, UserLoginForm, OrderForm, OrderDetailsForm, InvoiceForm
from django.contrib.gis.geoip2 import GeoIP2
from .cart import Cart
from .deliveryschedule import DeliverySchedule

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
    pincode = 'Delivery Pincode'
    if request.session.get('pincode') != '' and request.session.get('pincode') != None:
        pincode = request.session.get('pincode')

    featureItems = Item.objects.filter(featureItem=True).exclude(userID_id = request.user.pk)
    if request.user.is_authenticated:
        user_name = request.user.last_name
        user_type = request.user.userType
        #if pincode == 'Delivery Pincode':
        pincode = request.user.pinCode1
        request.session['pincode'] = pincode
        if user_type == '1':
            items = items.exclude(userID_id = request.user.pk)
        featureItems = Item.objects.filter(featureItem=True).exclude(userID_id = request.user.pk).filter(userID_id__pinCode=pincode)
    
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
    user_name = 'Guest!'#display the username
    pincode='Delivery Pincode'
    pincode_area = ''
    if category is not None:
        items = Item.objects.filter(itemCat=category)
    if fpo is not None:
        items = Item.objects.filter(userID_id=fpo)
    if region is not None:
        items = Item.objects.filter(userID_id__pinCode=region)
        pincode_area = PinCodeAPI(region)
        pincode=region
    form = ItemForm()

    if request.user.is_authenticated:
        user_name = request.user.last_name
        user_type = request.user.userType
        pincode = request.session.get('pincode') #get the logged in user's pincode
        if region is not None: #if the user is logged in and explicitly enters a pincode, then the items of that pincode will be displayed, not the user's own pincode
            pincode = region
            request.session['pincode'] = pincode
        items = Item.objects.filter(userID_id__pinCode=pincode) #if the user is logged in, then only the items available in user's pincode will be available to it.
        if user_type == '1':
            items = items.exclude(userID_id = request.user.pk)
    else:#if the user is not logged in and explicitly enters the pincode
        pincode = region
        request.session['pincode'] = pincode

    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    region_list = fpo = fpo_list()
    min_price = items.aggregate(Min('itemPrice'))['itemPrice__min']
    max_price = items.aggregate(Max('itemPrice'))['itemPrice__max']
    shop_page_context ={'items': items, 
                        'form': form, 
                        'login_user':user_name, 
                        'total_qty':total_qty, 
                        'fpo_list':fpo, 
                        'regions':region_list,
                        'total_price':total_price,
                        'min_price':min_price,
                        'max_price':max_price,
                        'pincode_area':pincode_area,
                        'clicked':'Shop',
                        'pincode':pincode
                        }
    return render(request, 'shop-grid.html', shop_page_context)

def PinCodeAPI(pincode):
    api_response = requests.get(f'https://api.postalpincode.in/pincode/{pincode}') 
    postalData = api_response.json()
    postoffice_data = postalData[0]['PostOffice']
    return postoffice_data[0]['Name']+", "+postoffice_data[0]['Block']

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
    user_name = 'Guest!'#display the username
    pincode='Delivery Pincode'
    if request.user.is_authenticated:
        user_name=request.user.last_name
        pincode = request.session.get('pincode')
    shop_details_context = {
        'item':item,
        'related_items':related_items,
        'login_user':user_name,
        'pincode':pincode,
        'clicked':'Shop',
        'total_qty':total_qty,
        'total_price':total_price
    }
    return render(request, 'shop-details.html', shop_details_context)

def shopping_cart(request):
    cart = Cart(request)
    total_qty = cart.__len__()
    total_price = cart.get_total_price()
    ds = DeliverySchedule()
    user_name = 'Guest!'#display the username
    pincode='Delivery Pincode'
    if request.user.is_authenticated:
        user_name = request.user.last_name
        pincode = request.session.get('pincode')
    shopping_cart_context = {
        'cart': cart, 
        'total_qty':total_qty, 
        'total_price':total_price, 
        'user_authenticated':request.user.is_authenticated, 
        'dateSeries':ds.dateSeries, 
        'timeSeries':ds.timeSeries, 
        'login_user':user_name,
        'pincode':pincode
    }
    return render(request, 'shopping-cart.html', context=shopping_cart_context)

def contact(request):
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    user_name = 'Guest!'#display the username
    pincode='Delivery Pincode'
    pincode = request.session.get('pincode')
    if request.user.is_authenticated:
        user_name = request.user.last_name
    contact_context = {
        'clicked':'Contact',
        'total_qty':total_qty,
        'total_price':total_price,
        'login_user':user_name,
        'pincode':pincode
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
    return render(request, 'checkout.html', {})

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
    user_form_context = {
        'user':user,
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
                UserAddresses.objects.create(userID_id=user.pk,userAddress1=user.userAddress1, userCity1=user.userCity1, userState1=user.userState1, pinCode1=user.pinCode1)
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
        # else:
        #     userInstance = get_object_or_404(CustomUser, id=request.user.pk)
        #     form = UserRegistrationForm(request.POST, instance=userInstance)
        #     user = form.save(param_password=request.POST['phone'])
        #     login(request, user)
        #     user_name = request.user.last_name
        #     return redirect('profile')

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
        if(request.user.is_authenticated):#Point: After logging in trying to edit the profile
            user = request.user
            user_name = request.user.last_name
            userInstance = get_object_or_404(CustomUser, id=request.user.pk)
            form = UserRegistrationForm(instance=userInstance)
            pass
        else:
            form = UserRegistrationForm()#new register point: opening the registratino page without login
            user_name = 'Guest!'
            pass    
    
    addresses = UserAddresses.objects.filter(userID = request.user.pk)
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    register_context = {
        'userform': form,
        'user':user,
        'login_user':user_name,
        'total_qty':total_qty,
        'total_price':total_price,
        'states':STATES,
        'gst_tmts':GST_TREATMENT,
        'user_types':USERTYPES,
        'addresses':addresses
    }
    return render(request, 'user-form.html', context=register_context)

def approve_user(request, userID):
    CustomUser.objects.filter(pk=userID).update(userApproved=True,approvedOn=datetime.now())
    return redirect('admin-master')

def activate_user(request, userID, activate):
    if activate == 0:
        CustomUser.objects.filter(pk=userID).update(isActive=False,activatedOn=datetime.now())
    else:
        CustomUser.objects.filter(pk=userID).update(isActive=True,activatedOn=datetime.now())
    return redirect('admin-master')

def add_address(request):
    if request.user.is_authenticated:
        userID=request.user.pk
        userAddress1 = request.POST.get('shippingAddress')
        userCity1 = request.POST.get('shippingTown')
        userState1 = request.POST.get('shippingState')
        pinCode1 = request.POST.get('shippingPostcode')
        setDefault = True
        UserAddresses.objects.create(userID_id=userID, userAddress1=userAddress1, userCity1=userCity1,userState1=userState1,pinCode1=pinCode1,setDefault=setDefault)
        CustomUser.objects.filter(pk=userID).update(userAddress1=userAddress1, userCity1=userCity1,userState1=userState1,pinCode1=pinCode1)
    return redirect('user-form')    

def update_profile(request):
    if request.user.is_authenticated and request.method == 'POST':
        userID = request.user.pk
        last_name = request.POST.get('last_name')
        email=request.POST.get('email')
        phone1 = request.POST.get('phone1')
        CustomUser.objects.filter(pk=userID).update(last_name=last_name,email=email,phone1=phone1)
    return redirect('user-form')

def update_billiing_address(request):
    if request.user.is_authenticated and request.method == 'POST':
        userID = request.user.pk
        userAddress = request.POST.get('userAddress')
        userCity=request.POST.get('userCity')
        userState = request.POST.get('userState')
        pinCode = request.POST.get('pinCode')
        CustomUser.objects.filter(pk=userID).update(userAddress=userAddress, userCity=userCity, userState=userState, pinCode=pinCode)
    return redirect('user-form')

def fetch_shipping_address(request, id):
    if request.user.is_authenticated:
        address = get_object_or_404(UserAddresses, pk=id)
        userID = address.userID.pk
        userAddress = address.userAddress1
        userCity=address.userCity1
        userState = address.userState1
        pinCode = address.pinCode1
        address_context = {
            'userID':userID,
            'userAddress':userAddress,
            'userCity':userCity,
            'userState':userState,
            'pinCode':pinCode,
            'addressID':id
        }
    return JsonResponse({'address_context':address_context})

def update_shipping_address(request, id):
    if request.user.is_authenticated and request.method == 'POST':
        userID = request.user.pk
        id=request.POST.get('addressID')
        userAddress = request.POST.get('userAddress1')
        userCity=request.POST.get('userCity1')
        userState = request.POST.get('userState1')
        pinCode = request.POST.get('pinCode1')
        UserAddresses.objects.filter(pk=id, userID_id=userID).update(userAddress1=userAddress, userCity1=userCity, userState1=userState, pinCode1=pinCode)
    return redirect('user-form')

def set_default_address(request, id):
    if request.user.is_authenticated:
        userID = request.user.pk
        UserAddresses.objects.filter(userID_id=userID).update(setDefault=False)
        UserAddresses.objects.filter(pk=id, userID_id=userID).update(setDefault=True)
        address = get_object_or_404(UserAddresses, pk=id)
        CustomUser.objects.filter(id=userID).update(userAddress1=address.userAddress1,userCity1=address.userCity1,userState1=address.userState1,pinCode1=address.pinCode1)
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
            if user.userType == '1':
                if user.userApproved == True:
                    user_login = authenticate(request, username=username, password=password)
                    if user_login is not None:
                            login(request, user_login)
                            return redirect('index')
                    else:
                        form.add_error(None, 'Invalid username or password!')
                        messages.success(request, 'Invalid username or password!')
                else:
                    form.add_error(None, 'Waiting for Approval!')
                    messages.success(request, 'Waiting for Approval!')
            elif user.userType == '0' and user.is_superuser:
                user_login = authenticate(request, username=username, password=password)
                login(request, user_login)
                return redirect('admin-master')
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
    return render(request, 'login.html', {'loginform': form})

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
def admin_master(request):
    if request.user.is_authenticated:
        total_users = CustomUser.objects.all()
        no_of_fpo = CustomUser.objects.filter(userType=1).__len__()
        no_of_biz = CustomUser.objects.filter(userType=2).__len__()
        no_of_inst = CustomUser.objects.filter(userType=3).__len__()
        no_of_overseas = CustomUser.objects.filter(userType=4).__len__()
        no_of_indv = CustomUser.objects.filter(userType=5).__len__()
        console_context = {
            'total_users':total_users,
            'total_fpo':no_of_fpo,
            'total_business':no_of_biz,
            'total_institutions':no_of_inst,
            'total_overseas':no_of_overseas,
            'total_individual':no_of_indv,
        }
        return render(request, 'admin-master-console.html', console_context)
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
        """if the user is not an FPO then the page should not be displayed"""
        if request.user.userType != '1':
            return redirect('index')
    else:
        user_name = 'Guest!'
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
        'total_items':total_items,
        'total_featured_items':total_featured_items,
        'total_item_categories':total_item_categories,
        'total_instock_items':total_instock_items,
        'total_active_items':total_active_items
    }

    return render(request, 'item_list.html', context=item_list_context)

def pincode_item_list(request, pincode):
    query = f'SELECT A.* FROM omsapp_item AS A INNER JOIN omsapp_customuser AS B ON A.userID_id=B.id AND B.userType=1 AND B.pinCode={pincode};'
    with connection.cursor as cursor:
        cursor.execute(query)
        pincode_items = cursor.fetchall()
    user_name = request.user.last_name
    item_context = {'items':pincode_items, 'login_user':user_name}
    return JsonResponse(item_context)
#endregion

#region cart management with session id (without login and with login)
def add_to_cart(request, product_id):
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

def update_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Item, itemID=product_id)
    try:
        selectedQty = request.POST['selectQuantity']
    except Exception as ex:
        print(ex)
        selectedQty = 1
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
def CreateOrder(request, param_total_quantity, param_total_price, param_gst_amount, param_deduction):
    if request.method == 'POST' and request.user.is_authenticated:
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
            view_orderGrandTotal = float(view_orderAmount)+float(view_orderGSTAmount)-float(view_orderDeduction)
            view_orderDeliveryDate = request.POST['selectDeliveryDate']
            view_orderDeliveryTime = request.POST['selectDeliveryTime']
            order_context = Order(orderNo= view_orderNo,
                            orderDate=view_orderDate, 
                            orderStatus=view_orderStatus,
                            orderAmount=view_orderAmount,
                            orderGSTAmount=view_orderGSTAmount,
                            orderDeduction=view_orderDeduction,
                            orderGrandTotal=view_orderGrandTotal,
                            schDeliveryDate = view_orderDeliveryDate,
                            schDeliveryTime = view_orderDeliveryTime,
                            userID_id=request.user.pk)
            try:
                order_context.save()
                order_id = Order.objects.all().latest('orderID').orderID
                if SaveOrderDetails(request, order_id, user_id) == True:
                    return redirect('order_successful')
                    #return render(request,'success.html',success_context)#HttpResponse('<h2>Order Placed Successfully!</h2>')
                else:
                    return render(request,'404.html',{'source':'Order'})
            except Exception as ex:
                return render(request,'404.html',{'source':'Order'})
        else:
            return render(request,'404.html',{'source':'Invalid Form'})
        #return JsonResponse({'qty':param_total_quantity, 'amount':param_total_price, 'gst':param_gst_amount, 'total': param_total_price})


def SaveOrderDetails(request,param_orderID,param_user_id):
    if request.method == 'POST':
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
                        customerID_id = param_user_id.pk
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
                    itemPricewithGST = eachitem['total_price']
                )
                cart_items.remove(eachitem['product'])
                del eachitem
            return True
        except Exception as ex:
            print(ex)
            return False
            #print(ex)

def order_successful(request):
    user_name = request.user.last_name
    pincode = request.session.get('pincode')
    success_context = {
        'orderID': Order.objects.all().latest('orderID').orderID,
        'orderNo': Order.objects.all().latest('orderID').orderNo,
        'login_user': user_name,
        'pincode':pincode
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
        received_orders = SubOrder.objects.filter(vendorID=request.user.pk).__len__()#total orders received by the FPO
        pending_orders = SubOrder.objects.filter(orderStatus = 'Pending Order', vendorID=request.user.pk).__len__()
        invoiced_orders = SubOrder.objects.filter(orderStatus = 'Invoiced').__len__()
        delivered_orders = SubOrder.objects.filter(orderStatus = 'Delivered').__len__()
        rejected_orders = SubOrder.objects.filter(orderStatus = 'Rejected').__len__()
        orders = SubOrder.objects.filter(vendorID=request.user.pk)
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
        orderNo = Order.objects.get(orderID=orderID).orderNo
        orderFrom = Order.objects.get(orderID=orderID).userID.last_name
        suborderID = SubOrder.objects.get(orderID_id=orderID, vendorID_id=request.user.pk).suborderID
        suborder_details = SubOrder.objects.get(orderID_id=orderID, vendorID_id=request.user.pk)
        received_orders = OrderDetails.objects.filter(suborderID_id=suborderID).select_related('itemID')
        # received_orders = OrderDetails.objects.filter(orderdetails__orderID_id=orderID, orders__orderdetails__vendorID_id=request.user.pk)
        # query = f"SELECT C.itemName, B.itemQty, B.itemPrice, B.id, B.orderID_id, B.remark, A.orderNo, A.remark, B.itemPricewithGST FROM omsapp_order AS A INNER JOIN omsapp_orderdetails AS B ON A.orderID=B.orderID_id AND A.orderID={orderID} INNER JOIN omsapp_item AS C ON B.itemID_id=C.itemID AND C.userID_id={request.user.id} INNER JOIN omsapp_customuser AS D ON D.id=A.userID_id"
        # with connection.cursor() as cursor:
        #     cursor.execute(query)
        #     received_orders = cursor.fetchall()
        existing_invoices = Invoice.objects.filter(orderID=orderID)
        user_name = request.user.last_name
        invoiceForm = InvoiceForm()
        context = {
            'received_orders': received_orders,
            'suborder_remark':suborder_details.remark,
            'suborder_status':suborder_details.orderStatus,
            'orderFrom':orderFrom,
            'login_user':user_name, 
            'orderNo':orderNo, 
            'orderID':orderID, 
            'suborderID':suborderID, 
            'invoice':invoiceForm, 
            'existing_invoices':existing_invoices
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
        
        # userID=request.user.pk
        # query_no_of_order_status = f"SELECT COUNT(B.orderStatus) FROM omsapp_order AS A INNER JOIN omsapp_orderdetails AS B ON A.orderID=B.orderID_id AND A.orderID=2 AND B.orderStatus<>'' INNER JOIN omsapp_item AS C ON B.itemID_id=C.itemID AND C.userID_id={userID} INNER JOIN omsapp_customuser AS D ON D.id=A.userID_id;"
        # query_no_of_items = f"SELECT COUNT(B.id) FROM omsapp_order AS A INNER JOIN omsapp_orderdetails AS B ON A.orderID=B.orderID_id AND A.orderID=2 INNER JOIN omsapp_item AS C ON B.itemID_id=C.itemID AND C.userID_id={userID} INNER JOIN omsapp_customuser AS D ON D.id=A.userID_id;"
        # with connection.cursor() as cursor:
        #     cursor.execute(query_no_of_items)
        #     no_of_items_fetched = cursor.fetchone()[0]
        #     cursor.execute(query_no_of_order_status)
        #     no_of_order_status = cursor.fetchone()[0]
        # if no_of_order_status == no_of_items_fetched:
        #     order_update_status = Order.objects.filter(orderID=mainOrderID).update(remark='CheckedAll')
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

def upload_invoice(request,orderID):
    if request.method == "POST":
        form = InvoiceForm(request.POST, request.FILES)
        if form.is_valid():
            userid = request.user.pk
            form.save(userID=userid, orderID=orderID)
            update_status = Order.objects.filter(orderID=orderID).update(orderStatus='Invoiced')
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
    
def confirm_delivery_order(request, order_id):
    if request.user.is_authenticated:
        user_name = request.user.last_name
        suborder_delivery = SubOrder.objects.filter(pk=order_id).update(orderStatus='Delivered',remark='Delivered')
        main_order_id = get_object_or_404(SubOrder, pk=order_id).orderID.pk
        order_deilvery = Order.objects.filter(pk=main_order_id).update(orderStatus='Delivered')    
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
        user_type = USERTYPE_CHOICES(request.user.userType)
        user_address = f"{request.user.userAddress} {request.user.userCity} {STATE_CHOICES(request.user.userState)} {request.user.pinCode}"
        user_address1 = f"{request.user.userAddress1} {request.user.userCity1} {STATE_CHOICES(request.user.userState1)} {request.user.pinCode1}"
        user_phone = request.user.phone
        items = Item.objects.filter(itemActive=True).order_by('-itemInStock').values('itemName').distinct().order_by('itemName')
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
    return redirect('bulk-buy')

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
        cart = Cart(request)
        total_qty = cart.__len__()#display total number quantities added in the basket
        total_price = cart.get_total_price()
        bulk_orders_context = {
            'bulk_orders':bulk_orders,
            'login_user':user_name,
            'total_qty':total_qty,
            'total_price':total_price
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
        #invoices = Invoice.objects.select_related('orderID')
        user_name = request.user.last_name
        cart = Cart(request)
        total_qty = cart.__len__()#display total number quantities added in the basket
        total_price = cart.get_total_price()
        render_context = {
            'placed_orders':orders,
            'login_user':user_name,
            'total_qty':total_qty,
            'total_price':total_price,
            'pincode':pincode
        }
        return render(request, 'orders.html', context=render_context)
    else:
        return render(request,'orders.html',{})

def placed_order_details(request,orderID):
    #orders = Order.objects.filter(userID=request.user.id)
    order_details = OrderDetails.objects.select_related('itemID').filter(orderID_id=orderID)
    invoice_details = Invoice.objects.filter(orderID_id=orderID)
    #query = str(order_details.query)
    user_name = 'Guest!'
    if request.user.is_authenticated:
        user_name = request.user.last_name
        #order_invoices = order_invoices(request, orderID)
    cart = Cart(request)
    total_qty = cart.__len__()#display total number quantities added in the basket
    total_price = cart.get_total_price()
    render_context = {
        'order_details':order_details,
        'login_user':user_name,
        'invoices':invoice_details,
        'total_qty':total_qty,
        'total_price':total_price
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