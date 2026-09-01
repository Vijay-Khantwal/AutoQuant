import os
import json
import glob
import requests
from dotenv import load_dotenv
from dhan_mapper import get_dhan_security_id

# Load API keys from .env
load_dotenv()

DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")
# Strict Sandbox URL to prevent live executions
SANDBOX_ORDER_URL = "https://sandbox.dhan.co/v2/orders"

def place_sandbox_order(security_id: str, quantity: int, transaction_type: str = "BUY"):
    """Fires the exact order payload to the Dhan Sandbox environment."""
    headers = {
        "access-token": DHAN_ACCESS_TOKEN,
        "client-id": DHAN_CLIENT_ID,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "dhanClientId": DHAN_CLIENT_ID,
        "correlationId": f"swing_ai_{security_id}", # To track our bot's orders
        "transactionType": transaction_type,
        "exchangeSegment": "NSE_EQ",
        "productType": "CNC",          # Cash and Carry (Delivery)
        "orderType": "MARKET",         # Buy immediately at LTP
        "validity": "DAY",
        "securityId": security_id,
        "quantity": quantity,
        "disclosedQuantity": 0,
        "price": 0,
        "triggerPrice": 0,
        "afterMarketOrder": False
    }

    response = requests.post(SANDBOX_ORDER_URL, headers=headers, json=payload)
    return response.json()

def execute_daily_trades():
    print("="*60)
    print("🚀 INITIALIZING DHAN SANDBOX EXECUTION ENGINE")
    print("="*60)
    
    if not DHAN_CLIENT_ID or not DHAN_ACCESS_TOKEN:
        print("❌ Error: DHAN_CLIENT_ID or DHAN_ACCESS_TOKEN not found in .env")
        return

    # 1. Find the latest decisions file
    decision_files = sorted(glob.glob("decisions_*.json"))
    if not decision_files:
        print("❌ No Agent decisions file found. Run agent.py first.")
        return
        
    latest_file = decision_files[-1]
    print(f"📄 Loading AI Decisions from: {latest_file}\n")
    
    with open(latest_file, "r") as f:
        decisions = json.load(f)

    # 2. Iterate through trades and execute approvals
    for item in decisions:
        verdict = item.get('audit_verdict', {})
        ticker = item['metadata']['ticker']
        
        if verdict.get('decision') == "APPROVE":
            ltp = item['quantitative_inputs']['ltp']
            alloc_inr = verdict.get('recommended_allocation_inr', 0)
            
            # Position Sizing Math
            quantity = int(alloc_inr / ltp)
            
            if quantity > 0:
                print(f"⚙️ Preparing Trade: {ticker} | Alloc: ₹{alloc_inr} | Qty: {quantity}")
                
                # Fetch Dhan Security ID
                dhan_id = get_dhan_security_id(ticker)
                
                if dhan_id:
                    # Inject Order into Sandbox
                    print(f"   ↳ Injecting Order to Sandbox (Security ID: {dhan_id})...")
                    res = place_sandbox_order(security_id=dhan_id, quantity=quantity)

# Read Response
                    valid_statuses = ['TRANSIT', 'PENDING', 'TRADED']
                    if res.get('orderStatus') in valid_statuses:
                        order_id = res.get('orderId', 'UNKNOWN')
                        print(f"   ✅ SUCCESS! Order Placed. Dhan OrderID: {order_id}\n")
                    else:
                        print(f"   ❌ SANDBOX REJECTED: {res}\n")
                else:
                    print(f"   ❌ FAILED: Could not map {ticker} to a Dhan Security ID.\n")
        else:
            print(f"⏭️ SKIPPED: {ticker} (Agent Status: REJECT)\n")
            
if __name__ == "__main__":
    execute_daily_trades()