import os
import sys
import django
from tqdm import tqdm
from django.db import transaction
from django.conf import settings
import shutil

# Step 1: Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Step 2: Set environment variable for Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'omsproject.settings')

# Step 3: Setup Django
django.setup()

# Now you can import your models
from omsapp.models import SchoolUDISE, CustomUser, Item, OrderDelivery, OrderInvoice, FPOAuthorisationDocs
import csv

#UDISE Data Import
def import_udise_data():
    print("🔄 Deleting old data...")
    SchoolUDISE.objects.all().delete()

    file_path = 'omsproject/udisebasic.csv'
    BATCH_SIZE = 1000
    school_list = []

    # Get total lines for tqdm
    with open(file_path, 'r', encoding='utf-8') as f:
        total = sum(1 for _ in f) - 1  # minus header

    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in tqdm(reader, total=total, desc="📦 Importing UDISE Schools"):
            try:
                obj = SchoolUDISE(
                    state_name = row['state_name'],
                    state_code = row['state_code'],
                    district_name = row['district_name'],
                    district_code = row['district_code'] if row['district_code'] else None,
                    sub_dist_name = row['subdistrict_name'],
                    sub_dist_code = row['subdistrict_code'] if row['subdistrict_code'] else None,
                    village_name = row['village_name'],
                    udise_code = row['udise_school_code'],
                    school_name = row['school_name'],
                    school_cat = row['school_category'],
                    school_type = row['school_type'],
                    loc_lat = float(row['latitude']) if row['latitude'] else 0.0,
                    loc_long = float(row['longitude']) if row['longitude'] else 0.0,
                    total_students = int(row['class_students']) if row['class_students'] else 0,
                    class_from = int(row['class_from']) if row['class_from'] else 0,
                    class_to = int(row['class_to']) if row['class_to'] else 0,
                    pre_primary_students = int(row['pre_primary_students']) if row['pre_primary_students'] else 0,
                    i_students = int(row['i_students']) if row['i_students'] else 0,
                    ii_students = int(row['ii_students']) if row['ii_students'] else 0,
                    iii_students = int(row['iii_students']) if row['iii_students'] else 0,
                    iv_students = int(row['iv_students']) if row['iv_students'] else 0,
                    v_students = int(row['v_students']) if row['v_students'] else 0,
                    vi_students = int(row['vi_students']) if row['vi_students'] else 0,
                    vii_students = int(row['vii_students']) if row['vii_students'] else 0,
                    viii_students = int(row['viii_students']) if row['viii_students'] else 0,
                    ix_students = int(row['ix_students']) if row['ix_students'] else 0,
                    x_students = int(row['x_students']) if row['x_students'] else 0,
                    xi_students = int(row['xi_students']) if row['xi_students'] else 0,
                    xii_students = int(row['xii_students']) if row['xii_students'] else 0,
                    total_students_with_preprimary = int(row['class_with_pre_primary_students']) if row['class_with_pre_primary_students'] else 0
                )
                school_list.append(obj)

                if len(school_list) >= BATCH_SIZE:
                    SchoolUDISE.objects.bulk_create(school_list)
                    school_list = []

            except Exception as e:
                print(f"❌ Error processing row: {row}")
                print(f"    Error: {e}")

        # Insert remaining records
        if school_list:
            SchoolUDISE.objects.bulk_create(school_list)

    print("✅ Data import completed successfully.")

#LGD Data Import
# def import_lgd_odisha_data():
#     print("🔄 Deleting old data...")
#     LGDData.objects.all().delete()

#     file_path = 'omsproject/lgd_odisha.csv'
#     BATCH_SIZE = 1000
#     lgd_list = []

#     # Get total lines for tqdm
#     with open(file_path, 'r', encoding='utf-8') as f:
#         total = sum(1 for _ in f) - 1  # minus header

#     with open(file_path, newline='', encoding='utf-8') as csvfile:
#         reader = csv.DictReader(csvfile)

#         for row in tqdm(reader, total=total, desc="📦 Importing LGD Odisha Data"):
#             try:
#                 obj = LGDData(
#                     state_code = row['state_code'],
#                     state_name_english = row['state_name_english'],
#                     district_code = row['district_code'] if row['district_code'] else None,
#                     district_name_english = row['district_name_english'],
#                     subdistrict_code = row['subdistrict_code'] if row['subdistrict_code'] else None,
#                     subdistrict_name_english = row['subdistrict_name_english'],
#                 )
#                 lgd_list.append(obj)

#                 if len(lgd_list) >= BATCH_SIZE:
#                     LGDData.objects.bulk_create(lgd_list)
#                     lgd_list = []

#             except Exception as e:
#                 print(f"❌ Error processing row: {row}")
#                 print(f"    Error: {e}")

#         # Insert remaining records
#         if lgd_list:
#             LGDData.objects.bulk_create(lgd_list)

#     print("✅ Data import completed successfully.")

def create_user_directory():
    print("🔄 Creating directory...")
    userids = CustomUser.objects.filter(userType='1')
    for userid in userids:
        # fpo_directory_docs = os.path.join(settings.MEDIA_ROOT, 'fpodocs', str(userid.pk))
        # print(f'🔄 Creating docs directory for {userid.last_name}')
        # os.makedirs(fpo_directory_docs, exist_ok=True)

        # fpo_directory_deliveryimg = os.path.join(settings.MEDIA_ROOT, 'deliveryimg', str(userid.pk))
        # print(f'🔄 Creating delivery image directory for {userid.last_name}')
        # os.makedirs(fpo_directory_deliveryimg, exist_ok=True)

        # fpo_directory_invoice = os.path.join(settings.MEDIA_ROOT, 'uploads', str(userid.pk))
        # print(f'🔄 Creating static directory for invoices for {userid.last_name}')
        # os.makedirs(fpo_directory_invoice, exist_ok=True)


        fpo_directory_static = os.path.join(settings.MEDIA_ROOT, 'static', str(userid.pk))
        print(f'🔄 Creating static directory for items for {userid.last_name}')
        os.makedirs(fpo_directory_static, exist_ok=True)

        #now fetch the files and move
        path = os.path.join(settings.MEDIA_ROOT)+'/'
        print(f'main path is {path}')
        #item
        desitnationpath = fpo_directory_static+'/'
        itemfiles = Item.objects.filter(userID_id=userid.pk)
        for file in itemfiles:
            sourcepath = path+str(file.itemImg)
            print(f'source path is {sourcepath}')
            if os.path.isfile(sourcepath):
                print(f'file {os.path.basename(str(file.itemImg))} exists and ready to move')
                print(f'destination path is {desitnationpath}')


    print("✅ User Directory creation completed successfully.")

if __name__ == '__main__':
    import_udise_data()
