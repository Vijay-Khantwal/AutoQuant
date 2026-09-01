"""
portfolio/services.py
Paper position monitor checks TP, SL, and 15-day expiry against live prices.
Also tracks MFE (Maximum Favorable Excursion) for 15 days even if closed early.
"""
import logging
from datetime import date, timedelta

import yfinance as yf

from django.conf import settings

logger = logging.getLogger(__name__)


def fetch_price_history(ticker: str, start_date: date, end_date: date, entry_price: float = None) -> dict | None:
    """Fetch the latest price, and absolute high/low since entry."""
    try:
        # We add 1 day to end_date because yfinance end date is exclusive
        hist = yf.Ticker(ticker).history(start=start_date, end=end_date + timedelta(days=1))
        if not hist.empty:
            # SANITIZE DAY 0: The morning before the 3:10 PM entry can contain false spikes/dips.
            # If entry_price is provided, constrain the first day's High/Low to not exceed the entry_price
            # (or rather, assume the first day's excursion is bounded between entry_price and close)
            if entry_price is not None and len(hist) > 0:
                first_date = hist.index[0].date()
                if first_date == start_date:
                    close_0 = hist["Close"].iloc[0]
                    hist.loc[hist.index[0], "High"] = max(entry_price, close_0)
                    hist.loc[hist.index[0], "Low"] = min(entry_price, close_0)

            return {
                "close": float(hist["Close"].iloc[-1]),
                "high": float(hist["High"].max()),
                "low": float(hist["Low"].min())
            }
    except Exception as exc:
        logger.error("Price fetch failed for %s: %s", ticker, exc)
    return None


def monitor_positions(log_callback=None) -> dict:
    """
    Check all OPEN positions for TP / SL / expiry triggers.
    Also continuously tracks max_high and max_low for 15 days for ALL recent positions.
    Returns a summary dict with lists of closed and updated positions.
    """
    from apps.portfolio.models import Position, Trade, DailyPnL
    from apps.execution.services.fee_engine import calculate_fees

    def log(msg: str):
        logger.info(msg)
        if log_callback:
            log_callback(msg)

    today = date.today()
    cutoff_date = today - timedelta(days=25)

    recent_positions = Position.objects.filter(entry_date__gte=cutoff_date)
    open_count = recent_positions.filter(status="OPEN").count()
    
    log(f"Monitoring {recent_positions.count()} recent positions ({open_count} open) for live pricing and MFE tracking...")

    closed_tickers, updated_tickers = [], []
    total_unrealized = 0.0

    for pos in recent_positions:
        days_held = (today - pos.entry_date).days
        if days_held > pos.max_hold_days and pos.status == "CLOSED":
            continue
            
        p_data = fetch_price_history(pos.ticker, pos.entry_date, today, pos.entry_price)
        if p_data is None:
            if pos.status == "OPEN":
                log(f"  [X]  {pos.ticker}: Could not fetch price, skipping.")
            continue
            
        current_price = p_data["close"]
        import math
        if math.isnan(current_price):
            log(f"  [X]  {pos.ticker}: Price is NaN, skipping.")
            continue
            
        period_high = p_data["high"]
        period_low = p_data["low"]

        

        # --- 1. UPDATE 15-DAY MFE/MAE TRACKING (For ALL positions) ---
        # The true peak and dip since entry date! Bound it by entry_price just in case.
        pos.max_high_15d = max(pos.entry_price, period_high)
        pos.max_low_15d = min(pos.entry_price, period_low)

        if pos.threshold_hit is None:
            # Did it hit TP during this period?
            if period_high >= pos.tp_price:
                pos.threshold_hit = "TP"
                pos.threshold_hit_price = pos.tp_price
                pos.threshold_hit_date = today
            # Did it hit SL during this period?
            elif period_low <= pos.sl_price:
                pos.threshold_hit = "SL"
                pos.threshold_hit_price = pos.sl_price
                pos.threshold_hit_date = today

        # --- 2. UPDATE LIVE OPEN POSITIONS (Exit logic & P&L) ---
        if pos.status == "OPEN":
            unrealized_pnl = (current_price - pos.entry_price) * pos.quantity
            unrealized_pct = (current_price / pos.entry_price - 1) * 100

            pos.current_price = current_price
            pos.unrealized_pnl = round(unrealized_pnl, 2)
            pos.unrealized_pnl_pct = round(unrealized_pct, 2)
            pos.days_held = days_held

            exit_reason = None
            exit_price_actual = current_price
            
            # POSITIONS MUST STAY OPEN UNTIL 15 DAYS NO MATTER WHAT.
            if days_held >= pos.max_hold_days:
                exit_reason = "EXPIRY"
                # If they hit a threshold earlier, the virtual P&L locks it, but the physical exit
                # occurs at the current 15th day close price (or we can physically exit at threshold).
                # To match backtest reality where we exit at limit, the physical exit should technically
                # be the threshold price if it was hit.
                if pos.threshold_hit == "TP":
                    exit_price_actual = pos.tp_price
                elif pos.threshold_hit == "SL":
                    exit_price_actual = pos.sl_price

            if exit_reason:
                pos.status = "CLOSED"
                pos.save()

                fees = calculate_fees(pos.entry_price, exit_price_actual, pos.quantity)
                gross_pnl = (exit_price_actual - pos.entry_price) * pos.quantity

                Trade.objects.create(
                    position=pos,
                    strategy=pos.strategy,
                    ai_decision=pos.ai_decision,
                    ticker=pos.ticker,
                    exit_price=exit_price_actual,
                    exit_date=today,
                    exit_reason=exit_reason,
                    gross_pnl=round(gross_pnl, 2),
                    net_pnl_zerodha=fees["zerodha"]["net_pnl"],
                    net_pnl_dhan=fees["dhan"]["net_pnl"],
                    net_pnl_groww=fees["groww"]["net_pnl"],
                    net_pnl_angel=fees["angel"]["net_pnl"],
                    total_fee_zerodha=fees["zerodha"]["total_fee"],
                    total_fee_dhan=fees["dhan"]["total_fee"],
                    total_fee_groww=fees["groww"]["total_fee"],
                    total_fee_angel=fees["angel"]["total_fee"],
                    hold_days=days_held,
                )
                log(f"  [-] {pos.ticker}: CLOSED ({exit_reason}) | Gross P&L: Rs {gross_pnl:.2f}")
                closed_tickers.append(pos.ticker)
            else:
                pos.save()
                total_unrealized += unrealized_pnl
                updated_tickers.append(pos.ticker)
                log(f"  [~] {pos.ticker}: Rs {current_price:.2f} | {unrealized_pct:+.2f}% | Day {days_held}/{pos.max_hold_days}")
        else:
            pos.save()

    realized_today = sum(
        t.net_pnl_zerodha
        for t in __import__("apps.portfolio.models", fromlist=["Trade"]).Trade.objects.filter(exit_date=today)
    )
    DailyPnL.objects.update_or_create(
        date=today,
        defaults={
            "unrealized_pnl": round(total_unrealized, 2),
            "realized_pnl": round(realized_today, 2),
            "total_positions": open_count,
        },
    )

    log(f"Monitor complete. Closed: {len(closed_tickers)}, Active: {len(updated_tickers)}")
    

    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    channel_layer = get_channel_layer()
    if channel_layer:
        try:
            async_to_sync(channel_layer.group_send)(
                "portfolio_live",
                {"type": "portfolio_update", "data": {"action": "refresh"}}
            )
        except Exception as e:
            log(f"WebSocket broadcast failed: {e}")
    return {"closed": closed_tickers, "updated": updated_tickers}
