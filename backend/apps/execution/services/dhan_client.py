"""
execution/services/dhan_client.py
Thin wrapper around the Dhan Sandbox REST API.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _headers() -> dict:
    return {
        "access-token": settings.DHAN_ACCESS_TOKEN,
        "client-id": settings.DHAN_CLIENT_ID,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def place_order(
    security_id: str,
    quantity: int,
    transaction_type: str = "BUY",
    correlation_id: str = "",
) -> dict:
    """Place an order in the Dhan Sandbox. Returns the raw JSON response."""
    import datetime
    now = datetime.datetime.now()
    is_amo = now.time() < datetime.time(9, 15) or now.time() >= datetime.time(15, 30)
    
    # Move url resolution inside function to avoid module-level settings import crash in Celery
    url = f"{settings.DHAN_BASE_URL}/orders"
    
    payload = {
        "dhanClientId": settings.DHAN_CLIENT_ID,
        "correlationId": correlation_id,
        "transactionType": transaction_type,
        "exchangeSegment": "NSE_EQ",
        "productType": "CNC",
        "orderType": "MARKET",
        "validity": "DAY",
        "securityId": security_id,
        "quantity": quantity,
        "disclosedQuantity": 0,
        "price": 0.0,
        "triggerPrice": 0.0,
        "afterMarketOrder": is_amo,
        "amoTime": "OPEN" if is_amo else "",
        "boProfitValue": 0.0,
        "boStopLossValue": 0.0,
    }
    
    # In sandbox mode without valid API keys, just mock the return if keys aren't set
    # In live mode, we MUST have valid API keys
    if settings.PAPER_TRADE_MODE or not settings.DHAN_ACCESS_TOKEN or not settings.DHAN_CLIENT_ID:
        logger.warning(f"[PAPER TRADE] Mocking {transaction_type} order for {security_id}.")
        import time
        return {
            "orderId": f"PAPER-{int(time.time())}",
            "orderStatus": "TRADED"
        }

    try:
        resp = requests.post(url, json=payload, headers=_headers(), timeout=15)
        # Sandbox sometimes returns 200 with error details inside JSON
        data = resp.json()
        logger.info(f"Dhan Sandbox Response: {resp.status_code} - {data}")
        return data
    except Exception as exc:
        logger.error(f"Dhan API request failed: {exc}")
        return {"error": str(exc), "orderStatus": "FAILED"}


def get_all_orders() -> list:
    """Fetch all orders from the Dhan Sandbox."""
    url = f"{settings.DHAN_SANDBOX_URL}/orders"
    if not settings.DHAN_ACCESS_TOKEN:
        return []
        
    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        data = resp.json()
        if isinstance(data, list):
            return data
        return data.get("data", [])
    except Exception as exc:
        logger.error("Dhan API error fetching orders: %s", exc)
        return []


def get_order(order_id: str) -> dict:
    """Fetch a single order by Dhan order ID."""
    url = f"{settings.DHAN_BASE_URL}/orders/{order_id}"
    
    if settings.PAPER_TRADE_MODE or not settings.DHAN_ACCESS_TOKEN:
        return {"orderId": order_id, "orderStatus": "TRADED"}
        
    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        return resp.json()
    except Exception as exc:
        logger.error("Dhan API error fetching order %s: %s", order_id, exc)
        return {"error": str(exc)}
