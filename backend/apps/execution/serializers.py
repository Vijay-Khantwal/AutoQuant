from rest_framework import serializers
from .models import ExecutionRun, Order


class OrderSerializer(serializers.ModelSerializer):
    fee_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "run", "decision", "ticker", "dhan_security_id",
            "quantity", "price", "allocated_inr", "transaction_type",
            "dhan_order_id", "dhan_status", "dhan_raw_response",
            "fee_zerodha", "fee_dhan", "fee_groww", "fee_angel",
            "fee_breakdown", "created_at", "updated_at",
        ]

    def get_fee_breakdown(self, obj):
        return {
            "zerodha": obj.fee_zerodha,
            "dhan":    obj.fee_dhan,
            "groww":   obj.fee_groww,
            "angel":   obj.fee_angel,
        }


class ExecutionRunSerializer(serializers.ModelSerializer):
    orders = OrderSerializer(many=True, read_only=True)
    order_count   = serializers.SerializerMethodField()
    success_count = serializers.SerializerMethodField()

    class Meta:
        model = ExecutionRun
        fields = [
            "id", "research_run", "status", "celery_task_id", "log_output",
            "order_count", "success_count", "orders", "created_at", "updated_at",
        ]

    def get_order_count(self, obj):
        return obj.orders.count()

    def get_success_count(self, obj):
        return obj.orders.filter(dhan_status__in=["TRANSIT", "PENDING", "TRADED"]).count()
