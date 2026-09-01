from django.db import models
from apps.execution.models import Order
from apps.model_mgmt.models import StrategyProfile


class Position(models.Model):
    """An open (or closed) paper trading position."""

    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    ]
    
    strategy = models.ForeignKey(StrategyProfile, on_delete=models.CASCADE, null=True, related_name="positions")
    ai_decision = models.CharField(max_length=10, default="APPROVE")
    
    ticker = models.CharField(max_length=30)
    entry_price = models.FloatField()
    current_price = models.FloatField(default=0.0)
    quantity = models.IntegerField()
    entry_date = models.DateField()
    entry_order = models.ForeignKey(
        Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="positions"
    )

    # Targets set at entry
    tp_price = models.FloatField()   # take-profit target price
    sl_price = models.FloatField()   # stop-loss target price
    max_hold_days = models.IntegerField(default=15)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="OPEN")

    # Live P&L (updated by monitor task)
    unrealized_pnl = models.FloatField(default=0.0)
    unrealized_pnl_pct = models.FloatField(default=0.0)
    days_held = models.IntegerField(default=0)

    # 15-Day Long-Term Tracking (MFE/MAE) - populated even after close
    max_high_15d = models.FloatField(null=True, blank=True)
    max_low_15d = models.FloatField(null=True, blank=True)
    threshold_hit = models.CharField(max_length=10, null=True, blank=True)
    threshold_hit_price = models.FloatField(null=True, blank=True)
    threshold_hit_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Position {self.ticker} [{self.status}]"


class Trade(models.Model):
    """A closed trade with full P&L accounting."""

    EXIT_REASON_CHOICES = [
        ("TP", "Take Profit"),
        ("EXPIRY", "Time Expiry"),
        ("MANUAL", "Manual Close"),
        ("SL", "Stop Loss")
    ]
    
    strategy = models.ForeignKey(StrategyProfile, on_delete=models.CASCADE, null=True, related_name="trades")
    ai_decision = models.CharField(max_length=10, default="APPROVE")
    
    position = models.OneToOneField(Position, on_delete=models.CASCADE, related_name="trade")
    exit_price = models.FloatField()
    exit_date = models.DateField()
    exit_reason = models.CharField(max_length=10, choices=EXIT_REASON_CHOICES)

    gross_pnl     = models.FloatField()   # (exit - entry) * qty
    # Net P&L after fees for each broker profile
    net_pnl_zerodha = models.FloatField(default=0.0)
    net_pnl_dhan    = models.FloatField(default=0.0)
    net_pnl_groww   = models.FloatField(default=0.0)
    net_pnl_angel   = models.FloatField(default=0.0)

    total_fee_zerodha = models.FloatField(default=0.0)
    total_fee_dhan    = models.FloatField(default=0.0)
    total_fee_groww   = models.FloatField(default=0.0)
    total_fee_angel   = models.FloatField(default=0.0)

    hold_days = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-exit_date"]

    def __str__(self):
        return f"Trade {self.position.ticker} → {self.exit_reason} | Net(Z): ₹{self.net_pnl_zerodha:.2f}"


class DailyPnL(models.Model):
    """Snapshot of portfolio P&L for each calendar day (for equity curve)."""

    date = models.DateField(unique=True)
    unrealized_pnl = models.FloatField(default=0.0)
    realized_pnl = models.FloatField(default=0.0)
    total_positions = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"DailyPnL {self.date}: unrealized={self.unrealized_pnl:.2f}, realized={self.realized_pnl:.2f}"
