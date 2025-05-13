from django.forms import ModelForm, Form, TextInput, PasswordInput, CharField, Textarea, Select, FileInput, DateInput
from .models import Item, Order, CustomUser, OrderDetails, Invoice
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

#region User Creation Form
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

CustomUser = get_user_model()
class UserRegistrationForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ['userType','first_name','last_name','org_name','email', 'phone','phone1','gstin','supply_place','gst_tmt','userAddress','userCity','userState','pinCode','userAddress1','userCity1','userState1','pinCode1','userNote']
        widgets = {
            'userType':Select(attrs={
                'class': 'form-control',
                'autofocus': True,
                'id':'userType',
                'style':'width:100%',
            }, choices=USERTYPE_CHOICES),
            'first_name': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name',
                'id':'first_name'
            }),#first_name is the name
            'last_name': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display Name',
                'id':'last_name'
            }),#last_name is the display name
            'org_name': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Business Name (Organisation/Company/Institution Name)',
                'id':'org_name'
            }),#organisation name
            'email':TextInput(attrs={
                'type': 'email',
                'class': 'form-control',
                'placeholder': 'Email',
                'id':'email'
            }),
            'phone':TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone/Mobile Number',
                'id':'phone'
            }),
            'phone1':TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone/Mobile Number',
                'id':'phone1'
            }),
            'gstin':TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'GSTIN',
                'id':'gstin'
            }),
            'supply_place':Select(attrs={
                'class': 'form-control',
                'id':'supply_place'
            }, choices=STATES),
            'gst_tmt':Select(attrs={
                'class': 'form-control registration-select',
                'id':'gst_tmt'
            }, choices=GST_TREATMENT),
            'userAddress':TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Address',
                'id':'userAddress'
            }),
            'userCity':TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City',
                'id':'userCity'
            }),
            'userState':Select(attrs={
                'class': 'form-control registration-select',
                'id':'userState'
            }, choices=STATES),
            'pinCode':TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pincode',
                'id':'pinCode'
            }),
            'userAddress1':TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Address',
                'id':'userAddress1'
            }),
            'userCity1':TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City',
                'id':'userCity1'
            }),
            'userState1':Select(attrs={
                'class': 'form-control registration-select',
                'id':'userState1'
            }, choices=STATES),
            'pinCode1':TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pincode',
                'id':'pinCode1'
            }),
            'userNote':Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Note/Remark/Comment',
                'style':'height:5rem',
                'id':'userNote'
            })
        }
    def save(self, commit=True, param_password=None):
        user = super().save(commit=False)
        user.set_password(param_password)
        if commit:
            user.username = user.phone
            user.save()
        return user
        
class UserLoginForm(Form):
    username = CharField(max_length=20, label='Enter Mobile/Phone Number', widget=TextInput(attrs={
            'class': 'form-control w-full p-2 border border-gray-300 rounded mt-1',
            'placeholder': 'Enter Mobile/Phone Number',
            'id':'username'
        }))
    password = CharField(widget=PasswordInput(attrs={
            'class': 'form-control w-full p-2 border border-gray-300 rounded mt-1',
            'placeholder': 'Enter Password',
            'id':'password'
        }))


#endregion

#region Item Form
ITEM_TYPES = [
    ('1', 'Goods'),
    ('1', 'Services'),
]
ITEM_CATEGORIES=[
    ('Vegetables', 'Vegetables'),
    ('Fruits', 'Fruits'),
    ('Dairy', 'Dairy'),
    ('Spices', 'Spices'),
    ('Cereals', 'Cereals'),
    ('Pulses','Pulses'),
    ('Animal Sourced', 'Animal Sourced'),
    ('Forest Produces', 'Forest Produces'),
    ('Packaged Foods', 'Packaged Foods'),
    ('Others', 'Others'),
]
ITEM_UNITS = [
    ('None', 'None'),
    ('Box', 'Box'),
    ('Bag', 'Bag'),
    ('Pieces', 'Pieces'),
    ('Packet', 'Packet'),
    ('kg', 'kg'),
    ('g', 'g'),
    ('ltr', 'ltr'),
    ('ml', 'ml'),
    ('quintal', 'quintal'),
    ('m', 'm'),
]
TAX_PREFERENCES = [
    ('1', 'Taxable'),
    ('2', 'Non-taxable'),
    ('3', 'Out-of-scope'),
    ('4', 'Non-GST supply'),
]
TAX_RATES=[
    ('1', '0%'),
    ('2', '5%'),
    ('3', '12%'),
    ('4', '18%'),
    ('5', '28%'),
]
class ItemForm(ModelForm):
    class Meta:
        model = Item
        fields = ['itemName', 'itemType', 'itemCat', 'itemSku', 'itemHSNCode', 'itemUnit', 'itemTaxPref', 'itemTaxRate', 'itemCostPrice' ,'itemPrice', 'itemImg', 'stockValue','itemDesc']
        widgets = {
            'itemName': TextInput(attrs={
                'class': 'form-control',
                'autofocus': True,
                'placeholder': 'Enter the Item Name'
            }),
            'itemType':Select(attrs={
                'class': 'form-control',
                'id':'itemType'
            }, choices=ITEM_TYPES),
            'itemCat':Select(attrs={
                'class': 'form-control',
                'id':'itemCat'
            }, choices=ITEM_CATEGORIES),
            'itemSku': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the Item SKU'
            }),
            'itemHSNCode': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the Item HSN Code'
            }),
            'itemUnit':Select(attrs={
                'class': 'form-control',
                'id':'itemUnit'
            }, choices=ITEM_UNITS),
            'itemTaxPref':Select(attrs={
                'class': 'form-control',
                'id':'itemTaxPref'
            }, choices=TAX_PREFERENCES),
            'itemTaxRate':Select(attrs={
                'class': 'form-control',
                'id':'itemType'
            }, choices=TAX_RATES),
            'itemCostPrice': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the Item Cost Price'
            }),
            'itemPrice': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the Item Sale Price'
            }),
            'stockValue': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the Opening Stock'
            }),
            'itemDesc': Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Description',
                'style':'height:5rem',
                'id':'itemDesc'
            }),
        }

    def save(self, commit=True, userid=None):
        item = super().save(commit=False)
        if commit:
            item.userID_id = userid
            item.save()
        return item
#endregion

#region Order Form
class OrderForm(Form):
    class Meta:
        model = Order
        fields = ['orderNo','orderDate','receivingDate','orderStatus','orderAmount','orderGSTAmount','orderDeduction','orderGrandTotal']
        
class OrderDetailsForm(ModelForm):
    class Meta:
        model = OrderDetails
        fields = ['orderID', 'itemID','itemQty','itemPrice','itemGST','itemGSTAmount','itemPricewithGST']
#endregion

#region Invoice form
class InvoiceForm(ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoiceNo', 'invoiceDate', 'invoiceFile']
        widgets = {
            'invoiceNo': TextInput(attrs={
                'class': 'form-control',
                'autofocus': True
            }),
            'invoiceDate': DateInput(attrs={
                'class': 'form-control',
                'type':'date',
            }),
            'invoiceFile': FileInput(attrs={
                'class': 'form-control',
            }),
        }

    def save(self, commit=True, userID=None, orderID = None):
        invoice = super().save(commit=False)
        if commit:
            invoice.orderID_id = orderID
            invoice.userID_id = userID
            invoice.save()
        return invoice
#endregion