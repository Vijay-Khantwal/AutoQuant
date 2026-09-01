from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from celery.result import AsyncResult

from .models import SignalRun, Signal
from .serializers import SignalRunSerializer, SignalSerializer
from .tasks import run_prediction_task


class SignalRunViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SignalRunSerializer

    def get_queryset(self):
        qs = SignalRun.objects.all()
        strategy_id = self.request.query_params.get("strategy_id")
        if strategy_id:
            qs = qs.filter(strategy_id=strategy_id)
        return qs

    @action(detail=False, methods=["post"], url_path="trigger")
    def trigger(self, request):
        """Kick off a new prediction Celery task."""
        strategy_id = request.data.get("strategy_id")
        if not strategy_id:
            return Response({"error": "strategy_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        task = run_prediction_task.delay(strategy_id)
        return Response(
            {"task_id": task.id, "message": "Prediction job started."},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"], url_path="signals")
    def signals(self, request, pk=None):
        run = self.get_object()
        sigs = Signal.objects.filter(run=run).order_by("rank")
        return Response(SignalSerializer(sigs, many=True).data)

    @action(detail=False, methods=["get"], url_path="task-status/(?P<task_id>[^/.]+)")
    def task_status(self, request, task_id=None):
        result = AsyncResult(task_id)
        return Response({"task_id": task_id, "status": result.status, "result": result.result})
