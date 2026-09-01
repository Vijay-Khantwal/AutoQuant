from rest_framework import serializers
from .models import ResearchRun, StockDecision


class StockDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockDecision
        fields = [
            "id", "ticker", "action", "tier1_news_brief",
            "confidence_score", "risk_flags", "fundamental_summary",
            "news_sentiment_summary", "final_rationale", "recommended_allocation_inr",
            "fundamentals_json", "raw_verdict_json",
            "ltp", "win_probability", "percentile_rank", "created_at",
        ]


class ResearchRunSerializer(serializers.ModelSerializer):
    decisions = StockDecisionSerializer(many=True, read_only=True)
    decision_count = serializers.SerializerMethodField()
    approve_count  = serializers.SerializerMethodField()
    available_signals = serializers.SerializerMethodField()

    class Meta:
        model = ResearchRun
        fields = [
            "id", "signal_run", "status", "celery_task_id", "log_output",
            "decision_count", "approve_count", "decisions", "available_signals", "created_at", "updated_at",
        ]

    def get_available_signals(self, obj):
        if not obj.signal_run: return []
        researched = obj.decisions.values_list('ticker', flat=True)
        from apps.signals.models import Signal
        sigs = Signal.objects.filter(run=obj.signal_run).exclude(ticker__in=researched).order_by('rank')[:10]
        return [{"ticker": s.ticker, "ltp": s.ltp, "win_probability": s.win_probability, "percentile_rank": s.percentile_rank, "rank": s.rank} for s in sigs]

    def get_decision_count(self, obj):
        return obj.decisions.count()

    def get_approve_count(self, obj):
        return obj.decisions.filter(action="APPROVE").count()
