from django.db import models
from django.db.models import Model, CharField, AutoField, DecimalField, ForeignKey, CASCADE, OneToOneField, DateTimeField, PositiveIntegerField, DateField, FloatField, IntegerField, EmailField, BooleanField, ImageField, FileField
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.conf import settings
import datetime


#region Registration
USERTYPE_CHOICES = [
    ('1', 'FPO'),
    ('2', 'Business'),
    ('3', 'Institution'),
    ('4', 'Overseas'),
    ('5', 'Individual'),
]
STATES=[
    ('1', 'Andhra Pradesh'),
    ('2', 'Arunachal Pradesh'),
    ('3', 'Assam'),
    ('4', 'Bihar'),
    ('5', 'Chhattisgarh'),
    ('6', 'Goa'),
    ('7', 'Gujarat'),
    ('8', 'Haryana'),
    ('9', 'Himachal Pradesh'),
    ('10', 'Jharkhand'),
    ('11', 'Karnataka'),
    ('12', 'Kerala'),
    ('13', 'Madhya Pradesh'),
    ('14', 'Maharashtra'),
    ('15', 'Manipur'),
    ('16', 'Meghalaya'),
    ('17', 'Mizoram'),
    ('18', 'Nagaland'),
    ('19', 'Odisha'),
    ('20', 'Punjab'),
    ('21', 'Rajasthan'),
    ('22', 'Sikkim'),
    ('23', 'Tamil Nadu'),
    ('24', 'Telangana'),
    ('25', 'Tripura'),
    ('26', 'Uttar Pradesh'),
    ('27', 'Uttarakhand'),
    ('28', 'West Bengal'),
    ('29', 'Andaman and Nicobar Islands [UT]'),
    ('30', 'Chandigarh [UT]'),
    ('31', 'Dadra and Nagar Haveli and Daman and Diu [UT]'),
    ('32', 'Delhi [UT]'),
    ('33', 'Jammu and Kashmir [UT]'),
    ('34', 'Ladakh [UT]'),
    ('35', 'Lakshadweep [UT]'),
    ('36', 'Puducherry [UT]'),
]
GST_TREATMENT=[
    ('1', 'Registered Business (Regular)'),
    ('2', 'Registered Business (Composition)'),
    ('3', 'Unregistered Business'),
    ('4', 'Individual'),
]
"""class CustomUserManager(UserManager):
    def create_user(self, username, email = None, password = None, **extra_fields):
        return super().create_user(username, email, password, **extra_fields)"""

class CustomUser(AbstractUser):
    id=AutoField(primary_key=True)
    """"Basic details"""
    userType = CharField(max_length=20, choices=USERTYPE_CHOICES)
    first_name = CharField(max_length=50)#name
    last_name = CharField(max_length=50)#displayname
    org_name=CharField(max_length=50, default='', blank=True)#business name
    email = EmailField(max_length=50)#not mandatory
    phone = CharField(max_length=12, unique=True)
    phone1 = CharField(max_length=12, default='', blank=True)
    gstin = CharField(max_length=15, default='', blank=True)
    supply_place = CharField(max_length=70, choices=STATES)
    gst_tmt = CharField(max_length=20, choices=GST_TREATMENT)#gst treatment
    """Billing Address"""
    userAddress = CharField(max_length=200)
    userCity = CharField(max_length=50)
    userState = CharField(max_length=20, choices=STATES)
    pinCode = CharField(max_length=6)
    """Shipping Address"""
    userAddress1 = CharField(max_length=200)
    userCity1 = CharField(max_length=50)
    userState1 = CharField(max_length=20, choices=STATES)
    pinCode1 = CharField(max_length=6)
    userNote = CharField(max_length=300, default='', blank=True)#remarks from user
    """Account attributes"""
    password = CharField(max_length=20, default='Admin@1234')
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS=['first_name']

    def __str__(self):
        return self.phone

class Login(Model):
    id = AutoField(primary_key=True)
    email = CharField(max_length=50)
    phone = CharField(max_length=15)
    password = CharField(max_length=10)
    def __str__(self):
        return self.id

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
    userID = ForeignKey(CustomUser, on_delete=CASCADE)

    def __str__(self):
        return self.itemID
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
    created_at = DateTimeField(default=now)

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
    orderNo = CharField(max_length=10)
    orderDate = DateField(default=datetime.date.today)
    orderStatus = CharField(max_length=25, default='Pending Order')
    orderAmount = FloatField()
    orderGSTAmount = FloatField()
    orderDeduction = FloatField()
    orderGrandTotal = FloatField()
    schDeliveryDate = CharField(max_length=10, default=None, null=True)
    schDeliveryTime = CharField(max_length=10, default=None, null=True)
    remark = CharField(max_length=20, default=None, null=True)
    userID = ForeignKey(CustomUser, on_delete=CASCADE)
    def __str__(self):
        return f"{self.orderID}"
    
class OrderDetails(Model):
    orderID = ForeignKey(Order, on_delete=CASCADE)
    itemID = ForeignKey(Item, on_delete=CASCADE)
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
    
class Invoice(Model):
    invoiceID = AutoField(primary_key=True)
    orderID = ForeignKey(Order, on_delete=CASCADE)
    invoiceNo = CharField(max_length=10, default='0000000000')
    invoiceDate = CharField(max_length=10)
    invoiceFile = FileField(null=True, verbose_name='Invoice', upload_to='uploads/')
    userID = ForeignKey(CustomUser, on_delete=CASCADE)
    def __str__(self):
        return self.invoiceID
    
class Delivery(Model):
    deliveryID = AutoField(primary_key=True)
    inviceID = ForeignKey(Invoice, on_delete=CASCADE)
    orderID = ForeignKey(Order, on_delete=CASCADE)
    deliveryDate = DateField(default=datetime.date.today)
    deliveryTime = CharField(max_length=15)
    deliveryImg = ImageField(upload_to='static/')
    def __str__(self):
        return self.deliveryID
#endregion

#region Bulk Buy Model
class BulkBuy(Model): 
    bulkBuyID = AutoField(primary_key=True)
    bulkBuyNo = CharField(max_length=10, default='0000000000')
    bulkBuyDate = DateField(default=datetime.date.today)
    userID = ForeignKey(CustomUser, on_delete=CASCADE)
    def __str__(self):
        return f"{self.bulkBuyID}"
    
class BulkBuyDetails(Model):
    bbdID = AutoField(primary_key=True)#bbd:bulkbuydetails
    bulkBuyID = ForeignKey(BulkBuy, on_delete=CASCADE)
    itemName = CharField(max_length=20)
    itemSpec = CharField(max_length=100)
    itemPrice = FloatField()
    itemQty = IntegerField()

    def __str__(self):
        return f"{self.bbdID}"

class BulkBuyResponse(Model):
    bulkBuyID = ForeignKey(BulkBuy, on_delete=CASCADE)
    bbdID = ForeignKey(BulkBuyDetails, on_delete=CASCADE)
    response_userID = ForeignKey(CustomUser, on_delete=CASCADE)
    response_date = DateField(default=datetime.date.today)
    response_status = BooleanField()

    def __str__(self):
        return f"{self.bulkBuyID}"

#region Notification Model
class Notification(Model):
    id=AutoField(primary_key=True)
    dateTime = DateTimeField(default=now)
    notificationText = CharField(max_length=200)
    userID = ForeignKey(CustomUser, on_delete=CASCADE)
    def __str__(self):
        return self.id
#endregion
