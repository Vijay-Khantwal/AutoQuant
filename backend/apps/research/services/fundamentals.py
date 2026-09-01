"""
research/services/fundamentals.py — refactored tools/fundamentals.py
"""
import logging
from typing import Any, Dict

import yfinance as yf

logger = logging.getLogger(__name__)


def tool_deep_fundamentals(ticker: str) -> Dict[str, Any]:
    """Pulls balance sheet, cash flows and valuation metrics for an NSE ticker."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        
        return {
            "ticker": ticker,
            "status": "SUCCESS",
            "valuation": {
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "market_cap_inr": info.get("marketCap"),
            },
            "profitability_and_returns": {
                "roe_pct": info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None,
                "profit_margins_pct": info.get("profitMargins", 0) * 100 if info.get("profitMargins") else None,
                "operating_cash_flow_inr": info.get("operatingCashflow"),
                "free_cash_flow_inr": info.get("freeCashflow"),
            },
            "solvency": {
                "debt_to_equity": info.get("debtToEquity") / 100 if info.get("debtToEquity") is not None else None,
                "total_debt_inr": info.get("totalDebt"),
            },
            "ownership": {
                "insider_promoter_holding_pct": info.get("heldPercentInsiders", 0) * 100 if info.get("heldPercentInsiders") else None,
                "institutional_holding_pct": info.get("heldPercentInstitutions", 0) * 100 if info.get("heldPercentInstitutions") else None,
            }
        }
    except Exception as exc:
        logger.error("Fundamentals fetch failed for %s: %s", ticker, exc)
        return {"ticker": ticker, "status": "ERROR", "message": str(exc)}
