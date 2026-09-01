import yfinance as yf
import pandas as pd
from typing import Dict, Any

def tool_deep_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Pulls balance sheet, income statement, cash flow, and 
    valuation metrics for Indian equities.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        bs = stock.balance_sheet
        cf = stock.cashflow
        
        # 1. Balance sheet extraction
        latest_bs = bs.iloc[:, 0] if not bs.empty else pd.Series(dtype='float64')
        total_debt = float(latest_bs.get('Total Debt', latest_bs.get('Long Term Debt', 0.0)))
        equity = float(latest_bs.get('Stockholders Equity', latest_bs.get('Total Stockholder Equity', 1.0)))
        debt_to_equity = round(total_debt / equity, 2) if equity else 0.0
        
        # 2. Cash flow check
        latest_cf = cf.iloc[:, 0] if not cf.empty else pd.Series(dtype='float64')
        operating_cf = float(latest_cf.get('Operating Cash Flow', latest_cf.get('Total Cash From Operating Activities', 0.0)))
        free_cf = float(latest_cf.get('Free Cash Flow', 0.0))
        
        # 3. Ownership / Governance
        promoter_holding = info.get('heldPercentInsiders', 0.0) * 100
        institutional_holding = info.get('heldPercentInstitutions', 0.0) * 100

        return {
            "ticker": ticker,
            "status": "SUCCESS",
            "valuation": {
                "pe_ratio": info.get('trailingPE'),
                "forward_pe": info.get('forwardPE'),
                "pb_ratio": info.get('priceToBook'),
                "market_cap_inr": info.get('marketCap')
            },
            "profitability_and_returns": {
                "roe_pct": round(info.get('returnOnEquity', 0.0) * 100, 2) if info.get('returnOnEquity') else None,
                "profit_margins_pct": round(info.get('profitMargins', 0.0) * 100, 2) if info.get('profitMargins') else None,
                "operating_cash_flow_inr": operating_cf,
                "free_cash_flow_inr": free_cf
            },
            "solvency": {
                "debt_to_equity": debt_to_equity,
                "total_debt_inr": total_debt,
                "interest_coverage": info.get('interestCoverage')
            },
            "ownership": {
                "insider_promoter_holding_pct": round(promoter_holding, 2),
                "institutional_holding_pct": round(institutional_holding, 2)
            }
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "status": "ERROR",
            "message": str(e)
        }