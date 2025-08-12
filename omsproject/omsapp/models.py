from django.db import models
from django.db.models import Model, CharField, AutoField, DecimalField, ForeignKey, CASCADE, OneToOneField, DateTimeField, PositiveIntegerField, DateField, FloatField, IntegerField, EmailField, BooleanField, ImageField, FileField
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.conf import settings
#import datetime


#region Registration
USERTYPES = [
    ('', 'Select Usertype'),
    ('1', 'FPO'),
    ('2', 'Business'),
    ('3', 'School'),
    ('4', 'Overseas'),
    ('5', 'Individual'),
]
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
GST_TREATMENT=[
    ('', 'Select GST Treatment'),
    ('1', 'Registered Business (Regular)'),
    ('2', 'Registered Business (Composition)'),
    ('3', 'Unregistered Business'),
    ('4', 'Individual'),
]

class CustomUser(AbstractUser):
    id=AutoField(primary_key=True)
    #""""Basic details"""
    userType = CharField(max_length=20, choices=USERTYPES)
    udise_code = CharField(max_length=11, default='00000000000', blank=True)#only for the school
    first_name = CharField(max_length=50)#name
    last_name = CharField(max_length=50)#displayname
    org_name=CharField(max_length=50, default='', blank=True)#business name
    email = EmailField(max_length=50, default='', blank=True)#not mandatory
    phone = CharField(max_length=12, unique=True)
    phone1 = CharField(max_length=12, default='', blank=True)
    gstin = CharField(max_length=15, default='', blank=True)
    supply_place = CharField(max_length=70, choices=LIST_STATES)
    gst_tmt = CharField(max_length=20, choices=GST_TREATMENT)#gst treatment
    #"""Registered Address"""
    contactPerson = CharField(max_length=50, null=True, blank=True)
    contactNo = CharField(max_length=15, null=True, blank=True)
    userAddress = CharField(max_length=200,null=True)
    userCity = CharField(max_length=50,null=True)
    userCity_name = CharField(max_length=50,null=True)
    userState = CharField(max_length=20, choices=LIST_STATES,null=True)
    userState_name = CharField(max_length=50,null=True)
    userDistrict = CharField(max_length=20, null=True)
    userDistrict_name = CharField(max_length=50,null=True)
    pinCode = CharField(max_length=6,null=True)
    #"""Account attributes"""
    password = CharField(max_length=20, default='Admin@1234')
    userApproved = BooleanField(null=True)
    approvedOn = DateField(null=True)
    isActive=BooleanField(null=True)
    activatedOn=DateField(null=True)
    deactivateRemark = CharField(max_length=100, null=True,blank=True)
    bill_address_lat = FloatField(null=True, blank=True)
    bill_address_long = FloatField(null=True, blank=True)
    ship_address_lat = FloatField(null=True, blank=True)
    ship_address_long = FloatField(null=True, blank=True)
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS=['first_name']

    def __str__(self):
        return self.phone
    
    def save(self, *args, **kwargs):
        if not self.username:
            if self.userType == '3':
                self.username = self.udise_code
            else:
                self.username = self.phone
        super().save(*args, **kwargs)


class Login(Model):
    id = AutoField(primary_key=True)
    email = CharField(max_length=50)
    phone = CharField(max_length=15)
    password = CharField(max_length=10)
    def __str__(self):
        return self.id

class SchoolUDISE(Model):
    id=AutoField(primary_key=True)
    state_name = CharField(max_length=50)
    state_code = IntegerField(null=True)
    district_name = CharField(max_length=50)
    district_code = IntegerField(null=True)
    sub_dist_name=CharField(max_length=50)
    sub_dist_code = IntegerField(null=True)
    village_name = CharField(max_length=50)
    udise_code = CharField(max_length=11)
    school_name = CharField(max_length=50)
    total_students = IntegerField(default=0)
    school_cat = CharField(max_length=20)
    school_type = CharField(max_length=20)
    loc_lat = FloatField()
    loc_long = FloatField()
    class_from = IntegerField(null=True, blank=True)
    class_to = IntegerField(null=True, blank=True)
    pre_primary_students = IntegerField(default=0)
    i_students = IntegerField(default=0)
    ii_students = IntegerField(default=0)
    iii_students = IntegerField(default=0)
    iv_students = IntegerField(default=0)
    v_students = IntegerField(default=0)
    vi_students = IntegerField(default=0)
    vii_students = IntegerField(default=0)
    viii_students = IntegerField(default=0)
    ix_students = IntegerField(default=0)
    x_students = IntegerField(default=0)
    xi_students = IntegerField(default=0)
    xii_students = IntegerField(default=0)
    total_students_with_preprimary = IntegerField(default=0)
    def __str__(self):
        return f"{self.id}"

#Addresses of all users
class UserShippingAddresses(Model):
    id = AutoField(primary_key=True)
    userID = ForeignKey(CustomUser, on_delete=CASCADE)
    userAddress1 = CharField(max_length=200)
    userCity1 = CharField(max_length=50)
    userCity1_name = CharField(max_length=50,null=True)
    userState1 = CharField(max_length=20, choices=LIST_STATES)
    userState1_name = CharField(max_length=50,null=True)
    userDistrict1 = CharField(max_length=20, null=True)
    userDistrict1_name = CharField(max_length=50,null=True)
    pinCode1 = CharField(max_length=6)
    contactPerson1 = CharField(max_length=50, null=True, blank=True)
    contactNo1 = CharField(max_length=15, null=True, blank=True)
    address_lat1 = FloatField(null=True, blank=True)
    address_long1 = FloatField(null=True, blank=True)
    setDefault = BooleanField(default=False, null=True)
    def __str__(self):
        return self.userID

class UserBillingAddresses(Model):
    id = AutoField(primary_key=True)
    userID = ForeignKey(CustomUser, on_delete=CASCADE)
    userAddress = CharField(max_length=200)
    userCity = CharField(max_length=50)
    userCity_name = CharField(max_length=50,null=True)
    userState = CharField(max_length=20, choices=LIST_STATES)
    userState_name = CharField(max_length=50,null=True)
    userDistrict = CharField(max_length=20, null=True)
    userDistrict_name = CharField(max_length=50,null=True)
    pinCode = CharField(max_length=6)
    contactPerson = CharField(max_length=50, null=True, blank=True)
    contactNo = CharField(max_length=15, null=True, blank=True)
    address_lat = FloatField(null=True, blank=True)
    address_long = FloatField(null=True, blank=True)
    setDefault = BooleanField(default=False, null=True)
    def __str__(self):
        return self.userID

class FPOServingAddresses(Model):
    id = AutoField(primary_key=True)
    userID = ForeignKey(CustomUser, on_delete=CASCADE)
    userAddress1 = CharField(max_length=200)
    userCity1 = CharField(max_length=50)
    userCity1_name = CharField(max_length=50,null=True)
    userState1 = CharField(max_length=20, choices=LIST_STATES)
    userState1_name = CharField(max_length=50,null=True)
    userDistrict1 = CharField(max_length=20, null=True)
    userDistrict1_name = CharField(max_length=50,null=True)
    pinCode1 = CharField(max_length=6)
    contactPerson1 = CharField(max_length=50, null=True, blank=True)
    contactNo1 = CharField(max_length=15, null=True, blank=True)
    address_lat1 = FloatField(null=True, blank=True)
    address_long1 = FloatField(null=True, blank=True)
    zoom = models.IntegerField(default=13)
    radius = models.FloatField(default=5000)
    label = models.CharField(max_length=100, null=True, blank=True)
    isActive = BooleanField(default=True)
    def __str__(self):
        return self.userID

#All the documents of the FPO User
class FPOAuthorisationDocs(Model):
    id = AutoField(primary_key=True)
    userID = ForeignKey(CustomUser, on_delete=CASCADE)
    auth_name = CharField(max_length=50, default=None)
    auth_contact = CharField(max_length=12, default=None)
    auth_email = CharField(max_length=100, null=True, blank=True)

    board_resolution = FileField(null=True, verbose_name='Board Resolution', upload_to='fpodocs/')
    br_verified = BooleanField(null=True, verbose_name='Board Resolution Verified')
    br_verified_on = DateField(null=True, verbose_name='Board Resolution Verified On')
    br_remark = CharField(max_length=100, null=True, verbose_name='Board Resolution Remark')
    
    cin = FileField(null=True, verbose_name='CIN', upload_to='fpodocs/')
    cin_verified = BooleanField(null=True, verbose_name='CIN Verified')
    cin_verified_on = DateField(null=True, verbose_name='CIN Verified On')
    cin_remark = CharField(max_length=100, null=True, verbose_name='CIN Remark')
    
    pan = FileField(null=True, verbose_name='PAN', upload_to='fpodocs/')
    pan_verified = BooleanField(null=True, verbose_name='PAN Verified')
    pan_verified_on = DateField(null=True, verbose_name='PAN Verified On')
    pan_remark = CharField(max_length=100, null=True, verbose_name='PAN Remark')
    
    bank = FileField(null=True, verbose_name='Bank', upload_to='fpodocs/')
    bank_verified = BooleanField(null=True, verbose_name='Bank Verified')
    bank_verified_on = DateField(null=True, verbose_name='Bank Verified On')
    bank_remark = CharField(max_length=100, null=True, verbose_name='Bank Remark')
    
    fssai = FileField(null=True, verbose_name='FSSAI', upload_to='fpodocs/')
    fssai_verified = BooleanField(null=True, verbose_name='FSSAI Verified')
    fssai_verified_on = DateField(null=True, verbose_name='FSSAI Verified On')
    fssai_remark = CharField(max_length=100, null=True, verbose_name='FSSAI Remark')
    
    gst = FileField(null=True, blank=True,verbose_name='GST', upload_to='fpodocs/')
    gst_verified = BooleanField(null=True, verbose_name='GST Verified')
    gst_verified_on = DateField(null=True, verbose_name='GST Verified On')
    gst_remark = CharField(max_length=100, null=True, verbose_name='GST Remark')
    
    apmc = FileField(null=True, blank=True, verbose_name='APMC', upload_to='fpodocs/')
    apmc_verified = BooleanField(null=True, verbose_name='APMC Verified')
    apmc_verified_on = DateField(null=True, verbose_name='APMC Verified On')
    apmc_remark = CharField(max_length=100, null=True, verbose_name='APMC Remark')
    
    exim = FileField(null=True, blank=True, verbose_name='EXIM', upload_to='fpodocs/')
    exim_verified = BooleanField(null=True, verbose_name='EXIM Verified')
    exim_verified_on = DateField(null=True, verbose_name='EXIM Verified On')
    exim_remark = CharField(max_length=100, null=True, verbose_name='EXIM Remark')
    def __str__(self):
        return self.userID
#endregion

#region Item Model
class Item(Model):
    itemID = AutoField(primary_key=True)
    itemName = CharField(max_length=200)
    itemType = CharField(max_length=20, default='')
    itemCat = CharField(max_length=200)
    itemSku = CharField(max_length=20, default='')
    itemHSNCode= CharField(max_length=15, default='')
    itemUnit = CharField(max_length=200)
    itemTaxPref=CharField(max_length=10, default='')
    itemTaxRate=CharField(max_length=10, default='')
    itemCostPrice=DecimalField(max_digits=10, decimal_places=2, default=0)
    itemPrice = DecimalField(max_digits=10, decimal_places=2)
    itemImg = ImageField(upload_to='static/')
    itemActive = BooleanField(default=True)
    itemInStock = BooleanField(default=True)
    stockValue = IntegerField(default=0)
    marketType = CharField(max_length=20, default='All')
    featureItem = BooleanField(default=True)
    itemDesc = CharField(max_length=200, default='')
    userID = ForeignKey(CustomUser, on_delete=CASCADE, related_name='user')

    def __str__(self):
        return self.itemID
#endregion

#regigion Item Pincode Map
class ItemPincodeMap(Model):
    id = AutoField(primary_key=True)
    itemID = ForeignKey(Item, on_delete=CASCADE, related_name='item_pincode_map')
    pincode = CharField(max_length=6)
    isActive = BooleanField(default=True)

    def __str__(self):
        return f"{self.itemID} - {self.pincode}"
#endregion

#region Item Category
class ItemCategory(Model):
    id = AutoField(primary_key=True)
    categoryCode = CharField(max_length=2, unique=True)
    categoryName = CharField(max_length=100, unique=True)
    categoryDesc = CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.categoryName
#endregion

#region Item Stock
class ItemStock(Model):
    itemID = ForeignKey(Item, on_delete=CASCADE)
    stockValue = PositiveIntegerField(default=0)

    def __str__(self):
        return self.stockValue
#endregion

#region Cart Model

class Cart(Model):
    #user = OneToOneField(User, on_delete=CASCADE, related_name="cart")
    user = OneToOneField(CustomUser, on_delete=CASCADE, related_name="cart")
    created_at = DateField(default=now)

    def __str__(self):
        return f"Cart of {self.user.username}"

    def total_price(self):
        return  sum(item.total_price() for item in self.items.all())
    
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())
    

class CartItem(Model):
    cart = ForeignKey(Cart, related_name="items", on_delete=CASCADE)
    product = CharField(max_length=255)
    quantity = PositiveIntegerField(default=0)
    price_per_unit = DecimalField(max_digits=10, decimal_places=2)
    itemID = ForeignKey(Item, on_delete=CASCADE)

    def __str__(self):
        return f"{self.quantity} of {self.product}"

    def total_price(self):
        return self.quantity * self.price_per_unit

#endregion

#region Order Model, Invoice Model, Delivery Model
class Order(Model):
    orderID = AutoField(primary_key=True)
    orderNo = CharField(max_length=11)
    orderDate = DateField(auto_now_add=True)
    orderStatus = CharField(max_length=25, default='Pending Order')
    orderAmount = FloatField()
    orderGSTAmount = FloatField()
    orderDeduction = FloatField()
    orderTransportation = FloatField(default=0)
    orderGrandTotal = FloatField()
    schDeliveryDate = CharField(max_length=10, default=None, null=True)
    schDeliveryTime = CharField(max_length=10, default=None, null=True)
    remark = CharField(max_length=20, default=None, null=True)
    userID = ForeignKey(CustomUser, on_delete=CASCADE, related_name='customer')#customer who ordered
    orderNote = CharField(max_length=200, null=True, blank=True)
    paymentMode = IntegerField(blank=True, null=True)#whether cod-1, institutional credit-2 or online-3
    paymentStatus=BooleanField(blank=True, null=True)#true:complete, false:incomplete, none:incomplete
    paymentDate=DateTimeField(blank=True, null=True)#datetime of the paytment made during delivery
    paymentRefNo=CharField(max_length=50, blank=True, null=True)#reference number for online transactions
    def __str__(self):
        return f"{self.orderID}"

class SubOrder(Model):
    suborderID = AutoField(primary_key=True)
    orderID = ForeignKey(Order, on_delete=CASCADE, related_name='suborders')
    vendorID = ForeignKey(CustomUser, on_delete=CASCADE, related_name='vendor_orders')
    customerID = ForeignKey(CustomUser, on_delete=CASCADE, related_name='customer_orders')
    orderStatus = CharField(max_length=25, default='Pending Order')
    remark = CharField(max_length=20, default=None, null=True)
    orderNote = CharField(max_length=200, null=True, blank=True)
    paymentMode = IntegerField(blank=True, null=True)#whether cod-1, institutional credit-2 or online-3
    paymentStatus=BooleanField(blank=True, null=True)#true:complete, false:incomplete, none:incomplete
    paymentDate=DateTimeField(blank=True, null=True)#datetime of the paytment made during delivery
    paymentRefNo=CharField(max_length=50, blank=True, null=True)#reference number for online transactions
    def __str__(self):
        return self.suborderID

class OrderDetails(Model):
    orderID = ForeignKey(Order, on_delete=CASCADE,related_name='orderdetails')
    suborderID = ForeignKey(SubOrder, on_delete=CASCADE, null=True, related_name='orderdetails')
    itemID = ForeignKey(Item, on_delete=CASCADE, related_name='orderdetails')
    itemQty = IntegerField()
    itemPrice = FloatField()
    itemGST = FloatField()
    itemGSTAmount = FloatField()
    itemPricewithGST = FloatField()
    deliveryDate = CharField(max_length=11)
    deliveryTime = CharField(max_length=15)
    orderStatus = CharField(max_length=25, default='Pending Order')
    remark = CharField(max_length=100, default=None, null=True)

    def __str__(self):
        return self.orderID,self.itemID
    
class OrderInvoice(Model):
    invoiceID = AutoField(primary_key=True)
    orderID = ForeignKey(Order, on_delete=CASCADE)
    suborderID = ForeignKey(SubOrder, on_delete=CASCADE,null=True)
    invoiceNo = CharField(max_length=10, default='0000000000')
    invoiceDate = CharField(max_length=10)
    invoiceFile = FileField(null=True, verbose_name='Invoice', upload_to='uploads/')
    userID = ForeignKey(CustomUser, on_delete=CASCADE)
    def __str__(self):
        return self.invoiceID
    
class OrderDelivery(Model):
    deliveryID = AutoField(primary_key=True)
    orderID = ForeignKey(Order, on_delete=CASCADE)
    suborderID = ForeignKey(SubOrder, on_delete=CASCADE, null=True)
    deliveryDate = DateTimeField(default=now)
    deliveryImg = ImageField(upload_to='deliveryimg/', null=True, blank=True)
    latitude = FloatField(null=True)
    longitude = FloatField(null=True)
    timestamp = DateTimeField(null=True, blank=True)
    def __str__(self):
        return self.deliveryID
#endregion

#region Bulk Buy Model
class BulkBuy(Model): 
    bulkBuyID = AutoField(primary_key=True)
    bulkBuyNo = CharField(max_length=11, default='0000000000')
    bulkBuyDate = DateTimeField(default=now)
    bulkBuyExpDate = DateField(null=True)
    userID = ForeignKey(CustomUser, on_delete=CASCADE) #customer who has placed the bulk order
    response_accept = BooleanField(null=True) #True when bulk buy offer of the vendor is accepted by the customer
    def __str__(self):
        return f"{self.bulkBuyID}"
    
class BulkBuyDetails(Model):
    bbdID = AutoField(primary_key=True)#bbd:bulkbuydetails
    bulkBuyID = ForeignKey(BulkBuy, on_delete=CASCADE, related_name='bulkbuyid_bbd')
    itemName = CharField(max_length=20)
    itemSpec = CharField(max_length=100)
    itemPrice = FloatField()
    itemQty = IntegerField()
    itemUnit=CharField(max_length=10, null=True)

    def __str__(self):
        return f"{self.bbdID}"

class BulkBuyResponse(Model):
    bbrID = AutoField(primary_key=True)
    bulkBuyID = ForeignKey(BulkBuy, on_delete=CASCADE, related_name='bulkbuyid_bbr')
    response_userID = ForeignKey(CustomUser, on_delete=CASCADE)
    response_date = DateTimeField(default=now)
    response_remark = CharField(max_length=250, default='Pending') #response from the customer whether to accept or not
    response_status = BooleanField() #responded from the vendor
    response_remark_date=DateField(null=True)

    def __str__(self):
        return f"{self.bbrID}"

class BulkBuyResponseDetails(Model):
    bbrdID = AutoField(primary_key=True)
    bbrID = ForeignKey(BulkBuyResponse, on_delete=CASCADE, related_name='bulkbuyid_bbrd')
    bbdID = ForeignKey(BulkBuyDetails, on_delete=CASCADE)
    itemPrice_indicative = FloatField()
    itemPrice_response = FloatField()
    itemQty_indicative = IntegerField(default=0)
    itemQty_response = IntegerField(default=0)
    
    def __str__(self):
        return f"{self.bbrdID}"

#endregion

#region Notification Model
class Notification(Model):
    id=AutoField(primary_key=True)
    dateTime = DateField(default=now)
    notificationText = CharField(max_length=200)
    userID = ForeignKey(CustomUser, on_delete=CASCADE)
    def __str__(self):
        return self.id
    
class UserMessage(Model):
    id=AutoField(primary_key=True)
    msgDate = DateTimeField(default=now)
    name=CharField(max_length=100, verbose_name='Sender Name')
    email=CharField(max_length=100, verbose_name='Sender Email')
    msg = CharField(max_length=500, verbose_name='Message')
    def __str__(self):
        return self.id
#endregion