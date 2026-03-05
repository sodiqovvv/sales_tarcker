import os
import json
from google.oauth2 import service_account
from google.cloud import firestore

# 1. Render'dagi Environment Variable'ni o'qiymiz
json_data = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")

if not json_data:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON topilmadi! Render muhitini tekshiring.")

# 2. JSON matnini lug'atga o'giramiz
key_dict = json.loads(json_data)

# 3. Kredensiallarni yaratamiz
creds = service_account.Credentials.from_service_account_info(key_dict)

# 4. Endi mijozni aynan shu creds bilan ishga tushiramiz
_db_client = firestore.Client(credentials=creds, project=key_dict["project_id"])

def get_db():
    return _db_client