import os
import requests
from dotenv import load_dotenv

load_dotenv()

DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")
SANDBOX_ORDERS_URL = "https://sandbox.dhan.co/v2/orders"

headers = {
    "access-token": DHAN_ACCESS_TOKEN,
    "client-id": DHAN_CLIENT_ID,
    "Content-Type": "application/json"
}

response = requests.get(SANDBOX_ORDERS_URL, headers=headers)
print("Sandbox Order Book Response:")
print(response.json())