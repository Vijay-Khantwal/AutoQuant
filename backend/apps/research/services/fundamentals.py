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
        
        # Fallback for Cash Flows if missing in info
        ocf = info.get("operatingCashflow")
        fcf = info.get("freeCashflow")
        if ocf is None or fcf is None:
            try:
                cf_df = t.cashflow
                if not cf_df.empty:
                    if ocf is None and 'Operating Cash Flow' in cf_df.index:
                        ocf = cf_df.loc['Operating Cash Flow'].iloc[0]
                    if fcf is None and 'Free Cash Flow' in cf_df.index:
                        fcf = cf_df.loc['Free Cash Flow'].iloc[0]
            except Exception:
                pass
                
        # Fallback for Debt to Equity
        dte = info.get("debtToEquity")
        if dte is not None:
            dte = dte / 100
        else:
            try:
                bs_df = t.balancesheet
                if not bs_df.empty:
                    total_debt = bs_df.loc['Total Debt'].iloc[0] if 'Total Debt' in bs_df.index else 0
                    equity = bs_df.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in bs_df.index else (bs_df.loc['Total Stockholder Equity'].iloc[0] if 'Total Stockholder Equity' in bs_df.index else 0)
                    if equity > 0:
                        dte = total_debt / equity
            except Exception:
                pass
        
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
                "operating_cash_flow_inr": float(ocf) if ocf is not None else None,
                "free_cash_flow_inr": float(fcf) if fcf is not None else None,
            },
            "solvency": {
                "debt_to_equity": float(dte) if dte is not None else None,
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
