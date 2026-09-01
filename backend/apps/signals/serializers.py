from rest_framework import serializers
from .models import SignalRun, Signal


class SignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signal
        fields = ["id", "ticker", "ltp", "win_probability", "percentile_rank", "rank", "created_at"]


class SignalRunSerializer(serializers.ModelSerializer):
    signals = SignalSerializer(many=True, read_only=True)
    signal_count = serializers.SerializerMethodField()

    class Meta:
        model = SignalRun
        fields = ["id", "run_date", "status", "celery_task_id", "log_output", "signal_count", "signals", "created_at", "updated_at"]

    def get_signal_count(self, obj):
        return obj.signals.count()
