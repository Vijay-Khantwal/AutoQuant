from django.db import models


class StrategyProfile(models.Model):
    name = models.CharField(max_length=100)
    tp_target = models.FloatField(default=0.03)
    sl_stop = models.FloatField(default=-0.02)
    hold_days = models.IntegerField(default=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.tp_target*100}%/{(self.sl_stop)*100}%)"


class ModelRun(models.Model):
    """One training run of the LightGBM model."""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    celery_task_id = models.CharField(max_length=255, blank=True)
    strategy = models.ForeignKey(StrategyProfile, on_delete=models.CASCADE, null=True, related_name="model_runs")

    # Validation metrics written at end of training
    fold1_base_rate   = models.FloatField(null=True, blank=True)
    fold1_precision   = models.FloatField(null=True, blank=True)
    fold2_base_rate   = models.FloatField(null=True, blank=True)
    fold2_precision   = models.FloatField(null=True, blank=True)
    fold3_base_rate   = models.FloatField(null=True, blank=True)
    fold3_precision   = models.FloatField(null=True, blank=True)
    total_samples     = models.IntegerField(null=True, blank=True)
    total_stocks      = models.IntegerField(null=True, blank=True)

    # Feature importances stored as JSON dict {feature_name: importance_score}
    feature_importances = models.JSONField(default=dict)

    notes = models.TextField(blank=True)
    trained_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ModelRun {self.id} [{self.status}] @ {self.trained_at}"


class TrainingLog(models.Model):
    """Individual log line streamed during a ModelRun."""

    model_run = models.ForeignKey(ModelRun, on_delete=models.CASCADE, related_name="logs")
    log_line = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"[{self.timestamp}] {self.log_line[:80]}"
