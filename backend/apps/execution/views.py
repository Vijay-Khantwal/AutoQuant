from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from celery.result import AsyncResult

from .models import ExecutionRun, Order
from .serializers import ExecutionRunSerializer, OrderSerializer
from .tasks import run_execution_task
from .services.dhan_client import get_all_orders


class ExecutionRunViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExecutionRunSerializer

    def get_queryset(self):
        qs = ExecutionRun.objects.all()
        strategy_id = self.request.query_params.get("strategy_id")
        if strategy_id:
            qs = qs.filter(research_run__signal_run__strategy_id=strategy_id)
        return qs

    @action(detail=False, methods=["post"], url_path="trigger")
    def trigger(self, request):
        decision_ids   = request.data.get("decision_ids")        # list of PKs or None
        research_run_id = request.data.get("research_run_id")    # or run ID
        task = run_execution_task.delay(decision_ids=decision_ids, research_run_id=research_run_id)
        return Response({"task_id": task.id, "message": "Execution job started."}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["get"], url_path="task-status/(?P<task_id>[^/.]+)")
    def task_status(self, request, task_id=None):
        result = AsyncResult(task_id)
        return Response({"task_id": task_id, "status": result.status, "result": result.result})


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @action(detail=False, methods=["get"], url_path="live")
    def live(self, request):
        """Fetch live order list from Dhan Sandbox API."""
        orders = get_all_orders()
        return Response({"orders": orders})
