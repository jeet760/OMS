from django.forms import ModelForm, Form, TextInput, PasswordInput, CharField, Textarea, Select, FileInput, DateInput
from .models import Item, Order, CustomUser, OrderDetails, Invoice, FPOAuthorisationDocs
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
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'autofocus': True,
                'id':'userType',
                'style':'width:100%',
            }, choices=USERTYPE_CHOICES),
            'first_name': TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Name',
                'id':'first_name'
            }),#first_name is the name
            'last_name': TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Display Name',
                'id':'last_name'
            }),#last_name is the display name
            'org_name': TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Business Name (Organisation/Company/Institution Name)',
                'id':'org_name'
            }),#organisation name
            'email':TextInput(attrs={
                'type': 'email',
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Email',
                'id':'email'
            }),
            'phone':TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Phone/Mobile Number',
                'id':'phone'
            }),
            'phone1':TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Phone/Mobile Number',
                'id':'phone1'
            }),
            'gstin':TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'GSTIN',
                'id':'gstin'
            }),
            'supply_place':Select(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'id':'supply_place'
            }, choices=STATES),
            'gst_tmt':Select(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 registration-select',
                'id':'gst_tmt'
            }, choices=GST_TREATMENT),
            'userAddress':TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Address',
                'id':'userAddress'
            }),
            'userCity':TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'City',
                'id':'userCity'
            }),
            'userState':Select(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 registration-select',
                'id':'userState'
            }, choices=STATES),
            'pinCode':TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Pincode',
                'id':'pinCode'
            }),
            'userAddress1':TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Address',
                'id':'userAddress1'
            }),
            'userCity1':TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'City',
                'id':'userCity1'
            }),
            'userState1':Select(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 registration-select',
                'id':'userState1'
            }, choices=STATES),
            'pinCode1':TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Pincode',
                'id':'pinCode1'
            }),
            'userNote':Textarea(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
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
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'autofocus': True,
                'placeholder': 'Enter the Item Name'
            }),
            'itemType':Select(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'id':'itemType'
            }, choices=ITEM_TYPES),
            'itemCat':Select(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'id':'itemCat'
            }, choices=ITEM_CATEGORIES),
            'itemSku': TextInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'placeholder': 'Enter the Item SKU'
            }),
            'itemHSNCode': TextInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'placeholder': 'Enter the Item HSN Code'
            }),
            'itemUnit':Select(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'id':'itemUnit'
            }, choices=ITEM_UNITS),
            'itemTaxPref':Select(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'id':'itemTaxPref'
            }, choices=TAX_PREFERENCES),
            'itemTaxRate':Select(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'id':'itemType'
            }, choices=TAX_RATES),
            'itemCostPrice': TextInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'placeholder': 'Enter the Item Cost Price'
            }),
            'itemPrice': TextInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'placeholder': 'Enter the Item Sale Price'
            }),
            'stockValue': TextInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'placeholder': 'Enter the Opening Stock'
            }),
            'itemDesc': Textarea(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
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
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'autofocus': True
            }),
            'invoiceDate': DateInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'type':'date',
            }),
            'invoiceFile': FileInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
            }),
        }

    def save(self, commit=True, userID=None, orderID = None):
        invoice = super().save(commit=False)
        if commit:
            invoice.orderID_id = orderID
            invoice.userID_id = userID
            invoice.save()
        return invoice
    
class FPOAuthrisationForm(ModelForm):
    class Meta:
        model = FPOAuthorisationDocs
        fields = ['auth_name','auth_contact','auth_email','board_resolution','cin','pan','bank','fssai','gst','apmc','exim']
        widgets = {
            'auth_name': TextInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'autofocus': True
            }),
            'auth_contact': TextInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'autofocus': True
            }),
            'auth_email': TextInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
                'autofocus': True
            }),
            'board_resolution': FileInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
            }),
            'cin': FileInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
            }),
            'pan': FileInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
            }),
            'bank': FileInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
            }),
            'fssai': FileInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
            }),
            'gst': FileInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
            }),
            'apmc': FileInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
            }),
            'exim': FileInput(attrs={
                'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none',
            }),
        }
    def save(self, commit = True, userID=None):
        fpodoc = super().save(commit=False)
        if commit:
            fpodoc.userID_id = userID
            fpodoc.save()
        return fpodoc
#endregion