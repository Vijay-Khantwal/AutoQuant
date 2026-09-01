from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from celery.result import AsyncResult

from .models import ModelRun, TrainingLog, StrategyProfile
from .serializers import ModelRunSerializer, TrainingLogSerializer, StrategyProfileSerializer
from .tasks import retrain_model_task

class StrategyProfileViewSet(viewsets.ModelViewSet):
    queryset = StrategyProfile.objects.all()
    serializer_class = StrategyProfileSerializer


class ModelRunViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ModelRunSerializer

    def get_queryset(self):
        qs = ModelRun.objects.all()
        strategy_id = self.request.query_params.get("strategy_id")
        if strategy_id:
            qs = qs.filter(strategy_id=strategy_id)
        return qs

    @action(detail=False, methods=["post"], url_path="retrain")
    def retrain(self, request):
        strategy_id = request.data.get("strategy_id")
        if not strategy_id:
            return Response({"error": "strategy_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        task = retrain_model_task.delay(strategy_id)
        return Response({"task_id": task.id, "message": "Model retraining started."}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"], url_path="logs")
    def logs(self, request, pk=None):
        run = self.get_object()
        logs = TrainingLog.objects.filter(model_run=run).order_by("timestamp")
        return Response(TrainingLogSerializer(logs, many=True).data)

    @action(detail=False, methods=["get"], url_path="task-status/(?P<task_id>[^/.]+)")
    def task_status(self, request, task_id=None):
        result = AsyncResult(task_id)
        return Response({"task_id": task_id, "status": result.status, "result": result.result})
