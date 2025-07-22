import os
import sys
import django
from tqdm import tqdm
from django.db import transaction

# Step 1: Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Step 2: Set environment variable for Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'omsproject.settings')

# Step 3: Setup Django
django.setup()

# Now you can import your models
from omsapp.models import SchoolUDISE
import csv

def import_data():
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
                    total_students = int(row['class_students']) if row['class_students'] else 0
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

if __name__ == '__main__':
    import_data()
