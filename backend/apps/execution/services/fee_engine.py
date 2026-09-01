"""
execution/services/fee_engine.py
Multi-broker fee simulator for NSE equity delivery trades.
All statutory charges are identical across brokers; only brokerage differs.
"""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class BrokerProfile:
    name: str
    # Brokerage: either flat per order OR percentage, whichever is lower
    flat_brokerage: float = 20.0    # ₹ per order
    pct_brokerage: float = 0.0003   # 0.03% of turnover


BROKER_PROFILES: Dict[str, BrokerProfile] = {
    "zerodha": BrokerProfile(name="Zerodha",  flat_brokerage=20.0, pct_brokerage=0.0003),
    "dhan":    BrokerProfile(name="Dhan",     flat_brokerage=20.0, pct_brokerage=0.0003),
    "groww":   BrokerProfile(name="Groww",    flat_brokerage=20.0, pct_brokerage=0.0),
    "angel":   BrokerProfile(name="Angel One",flat_brokerage=20.0, pct_brokerage=0.0),
}

# Statutory rates (identical for all brokers, NSE equity delivery)
STT_RATE_SELL       = 0.001      # 0.1% on sell-side turnover
NSE_EXCHANGE_RATE   = 0.0000335  # 0.00335%
GST_RATE            = 0.18       # 18% on brokerage
SEBI_RATE           = 10 / 1e7   # ₹10 per crore (= 0.000001 * 10)
STAMP_RATE_BUY      = 0.00015    # 0.015% on buy-side turnover


def _calc_brokerage(turnover: float, profile: BrokerProfile) -> float:
    pct_charge = turnover * profile.pct_brokerage
    return min(profile.flat_brokerage, pct_charge) if profile.pct_brokerage > 0 else profile.flat_brokerage


def calculate_fees(
    buy_price: float,
    sell_price: float,
    quantity: int,
) -> Dict[str, Dict]:
    """
    Returns a dict of {broker_key: {breakdown dict}} for a round-trip trade.
    """
    buy_turnover  = buy_price  * quantity
    sell_turnover = sell_price * quantity

    results = {}
    for key, profile in BROKER_PROFILES.items():
        buy_brokerage  = _calc_brokerage(buy_turnover,  profile)
        sell_brokerage = _calc_brokerage(sell_turnover, profile)
        total_brokerage = buy_brokerage + sell_brokerage

        stt           = sell_turnover * STT_RATE_SELL
        exchange_fees = (buy_turnover + sell_turnover) * NSE_EXCHANGE_RATE
        gst           = total_brokerage * GST_RATE
        sebi          = (buy_turnover + sell_turnover) * SEBI_RATE
        stamp_duty    = buy_turnover * STAMP_RATE_BUY
        total_fee     = total_brokerage + stt + exchange_fees + gst + sebi + stamp_duty

        gross_pnl = (sell_price - buy_price) * quantity
        net_pnl   = gross_pnl - total_fee

        results[key] = {
            "broker": profile.name,
            "buy_brokerage":  round(buy_brokerage,  2),
            "sell_brokerage": round(sell_brokerage, 2),
            "stt":            round(stt,            2),
            "exchange_fees":  round(exchange_fees,  2),
            "gst":            round(gst,            2),
            "sebi_charges":   round(sebi,           2),
            "stamp_duty":     round(stamp_duty,     2),
            "total_fee":      round(total_fee,      2),
            "gross_pnl":      round(gross_pnl,      2),
            "net_pnl":        round(net_pnl,        2),
        }
    return results


def get_entry_fees(buy_price: float, quantity: int) -> Dict[str, float]:
    """
    Returns only the buy-side fees (for recording on order entry).
    Returns {broker_key: total_entry_fee}.
    """
    buy_turnover = buy_price * quantity
    out = {}
    for key, profile in BROKER_PROFILES.items():
        brokerage  = _calc_brokerage(buy_turnover, profile)
        exchange   = buy_turnover * NSE_EXCHANGE_RATE
        gst        = brokerage * GST_RATE
        sebi       = buy_turnover * SEBI_RATE
        stamp      = buy_turnover * STAMP_RATE_BUY
        out[key]   = round(brokerage + exchange + gst + sebi + stamp, 2)
    return out
