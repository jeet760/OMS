import os
import sys
import django

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
    with open('omsproject/udisebasic.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            SchoolUDISE.objects.create(
                state_name = row['state_name'],
                district_name = row['district_name'],
                sub_dist_name = row['subdistrict_name'],
                village_name = row['village_name'],
                udise_code = row['udise_school_code'],
                school_name = row['school_name'],
                school_cat = row['school_category'],
                school_type = row['school_type'],
                loc_lat = float(row['latitude']),
                loc_long = float(row['longitude']),
            )
    print("Data imported successfully.")

if __name__ == '__main__':
    import_data()