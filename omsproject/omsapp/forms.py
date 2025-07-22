from django import forms
from django.forms import ModelForm, Form, TextInput, PasswordInput, CharField, Textarea, Select, FileInput, DateInput
from .models import Item, Order, CustomUser, OrderDetails, OrderInvoice, FPOAuthorisationDocs
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

#region User Creation Form
USERTYPE_CHOICES = [
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
    ('35','Andaman And Nicobar Islands'),
    ('4','Chandigarh'),
    ('7','Delhi'),
    ('1','Jammu And Kashmir'),
    ('37','Ladakh'),
    ('31','Lakshadweep'),
    ('34','Puducherry'),
    ('38','The Dadra And Nagar Haveli And Daman And Diu'),
]
LIST_DISTRICTS = [
    ('', 'Select District'),
]
LIST_SUBDISTRICT = [
    ('', 'Select Block/Sub-District'),
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
        fields = ['userType','udise_code','first_name','last_name','org_name','email', 'phone','phone1','gstin','supply_place','gst_tmt','userAddress','userCity','userState','userDistrict','pinCode']#,'userAddress1','userCity1','userState1','userDistrict1','pinCode1','userNote'
        widgets = {
            'userType':Select(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'autofocus': True,
                'id':'userType',
                'style':'width:100%',
            }, choices=USERTYPE_CHOICES),
            'udise_code': TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'UDISE Number',
                'id':'udise_code',
                'type':'number'
            }),#UDISE code of the school
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
                'placeholder': 'Business Name (Organisation/Company/School Name)',
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
                'class': 'supply_place w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'id':'supply_place'
            }, choices=LIST_STATES),
            'gst_tmt':Select(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 registration-select',
                'id':'gst_tmt'
            }, choices=GST_TREATMENT),
            'userAddress':TextInput(attrs={
                'class': 'userAddress w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Address',
                'id':'userAddress'
            }),
            'userCity':Select(attrs={
                'class': 'userCity w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 registration-select',
                'id':'userCity'
            }, choices=LIST_SUBDISTRICT),
            'userState':Select(attrs={
                'class': 'userState w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 registration-select',
                'id':'userState'
            }, choices=LIST_STATES),
            'userDistrict':Select(attrs={
                'class': 'userDistrict w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 registration-select',
                'id':'userDistrict'
            }, choices=LIST_DISTRICTS),
            'pinCode':TextInput(attrs={
                'class': 'pinCode w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Pincode',
                'id':'pinCode'
            }),
        }
    def save(self, commit=True, param_password=None):
        user = super().save(commit=False)
        user.set_password(param_password)
        # if user.udise_code == '00000000000':
        #     user.username = user.phone
        # else:
        #     user.username = user.udise_code
        if commit:
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

class ItemImportExcelForm(Form):
    excel_file = forms.FileField(label='Select File to Import Items',
                                 widget=forms.ClearableFileInput(attrs={'class': 'w-full p-2 rounded border border-gray-300 focus:outline-none'}))
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
        model = OrderInvoice
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

    def save(self, commit=True, userID=None, orderID = None, suborderID=None):
        invoice = super().save(commit=False)
        if commit:
            invoice.orderID_id = orderID
            invoice.userID_id = userID
            invoice.suborderID_id = suborderID
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