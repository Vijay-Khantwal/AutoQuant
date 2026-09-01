from rest_framework import serializers
from .models import ModelRun, TrainingLog, StrategyProfile

class StrategyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyProfile
        fields = ["id", "name", "tp_target", "sl_stop", "hold_days", "is_active", "created_at"]

class TrainingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingLog
        fields = ["id", "log_line", "timestamp"]


class ModelRunSerializer(serializers.ModelSerializer):
    logs = TrainingLogSerializer(many=True, read_only=True)
    fold_summary = serializers.SerializerMethodField()

    class Meta:
        model = ModelRun
        fields = [
            "id", "status", "celery_task_id",
            "fold1_base_rate", "fold1_precision",
            "fold2_base_rate", "fold2_precision",
            "fold3_base_rate", "fold3_precision",
            "total_samples", "total_stocks",
            "feature_importances", "fold_summary",
            "notes", "trained_at", "created_at", "updated_at",
            "logs",
        ]

    def get_fold_summary(self, obj):
        folds = []
        for i in range(1, 4):
            br = getattr(obj, f"fold{i}_base_rate", None)
            pr = getattr(obj, f"fold{i}_precision", None)
            if br is not None and pr is not None:
                folds.append({
                    "fold": i,
                    "base_rate": br,
                    "precision": pr,
                    "edge": round(pr - br, 2),
                })
        return folds
