import os
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')
PORT = int(os.getenv('PORT', 8080))
FAMILY_USER_IDS = os.getenv('FAMILY_USER_IDS', '').split(',')
FAMILY_USER_IDS = [f.strip() for f in FAMILY_USER_IDS if f.strip()]
MONTHLY_BUDGET = float(os.getenv('MONTHLY_BUDGET', '5000'))
