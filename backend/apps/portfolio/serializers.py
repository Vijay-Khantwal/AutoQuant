from rest_framework import serializers
from .models import Position, Trade, DailyPnL


class TradeSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(source="position.ticker", read_only=True)
    entry_price = serializers.FloatField(source="position.entry_price", read_only=True)
    fee_comparison = serializers.SerializerMethodField()

    class Meta:
        model = Trade
        fields = [
            "id", "ticker", "entry_price", "exit_price", "exit_date",
            "exit_reason", "gross_pnl", "hold_days",
            "net_pnl_zerodha", "net_pnl_dhan", "net_pnl_groww", "net_pnl_angel",
            "total_fee_zerodha", "total_fee_dhan", "total_fee_groww", "total_fee_angel",
            "fee_comparison", "created_at", "strategy", "ai_decision"
        ]

    def get_fee_comparison(self, obj):
        return {
            "zerodha": {"total_fee": obj.total_fee_zerodha, "net_pnl": obj.net_pnl_zerodha},
            "dhan":    {"total_fee": obj.total_fee_dhan,    "net_pnl": obj.net_pnl_dhan},
            "groww":   {"total_fee": obj.total_fee_groww,   "net_pnl": obj.net_pnl_groww},
            "angel":   {"total_fee": obj.total_fee_angel,   "net_pnl": obj.net_pnl_angel},
        }


class PositionSerializer(serializers.ModelSerializer):
    trade = TradeSerializer(read_only=True)

    class Meta:
        model = Position
        fields = [
            "id", "ticker", "entry_price", "current_price", "quantity",
            "entry_date", "tp_price", "sl_price", "max_hold_days",
            "status", "unrealized_pnl", "unrealized_pnl_pct",
            "days_held", "trade", "created_at", "updated_at",
            "strategy", "ai_decision",
            "max_high_15d", "max_low_15d", "threshold_hit", 
            "threshold_hit_price", "threshold_hit_date"
        ]


class DailyPnLSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyPnL
        fields = ["id", "date", "unrealized_pnl", "realized_pnl", "total_positions", "created_at"]


class PortfolioSummarySerializer(serializers.Serializer):
    total_open_positions  = serializers.IntegerField()
    total_closed_trades   = serializers.IntegerField()
    win_count             = serializers.IntegerField()
    loss_count            = serializers.IntegerField()
    win_rate_pct          = serializers.FloatField()
    total_realized_pnl    = serializers.FloatField()
    total_unrealized_pnl  = serializers.FloatField()
    total_virtual_pnl     = serializers.FloatField()
    total_unrealized_fees = serializers.FloatField(required=False)
    total_virtual_fees    = serializers.FloatField(required=False)
    avg_hold_days         = serializers.FloatField()
    equity_curve          = DailyPnLSerializer(many=True)


