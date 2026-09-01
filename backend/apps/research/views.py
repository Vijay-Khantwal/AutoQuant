from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from celery.result import AsyncResult
from django.conf import settings

from .models import ResearchRun, StockDecision
from .serializers import ResearchRunSerializer, StockDecisionSerializer
from .tasks import run_research_task


class ResearchRunViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ResearchRunSerializer

    def get_queryset(self):
        qs = ResearchRun.objects.all()
        strategy_id = self.request.query_params.get("strategy_id")
        if strategy_id:
            qs = qs.filter(signal_run__strategy_id=strategy_id)
        return qs

    @action(detail=False, methods=["post"], url_path="create-blank")
    def create_blank(self, request):
        from apps.signals.models import SignalRun
        latest_run = SignalRun.objects.filter(status="SUCCESS").first()
        if not latest_run:
            return Response({"error": "No signal run found."}, status=status.HTTP_400_BAD_REQUEST)
        run = ResearchRun.objects.create(status="SUCCESS", signal_run=latest_run)
        return Response({"id": run.id, "message": "Created blank run."}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="trigger")
    def trigger(self, request):
        from apps.signals.models import SignalRun
        strategy_id = request.data.get("strategy_id")
        signal_run_id = request.data.get("signal_run_id")
        
        if not signal_run_id and strategy_id:
            latest_signal = SignalRun.objects.filter(status="SUCCESS", strategy_id=strategy_id).first()
            if latest_signal:
                signal_run_id = latest_signal.id

        research_run_id = request.data.get("research_run_id")
        top_n = request.data.get("top_n", getattr(settings, 'TOP_CANDIDATES', 5))
        ticker_list = request.data.get("ticker_list")
        
        task = run_research_task.delay(signal_run_id=signal_run_id, research_run_id=research_run_id, top_n=top_n, ticker_list=ticker_list)
        return Response({"task_id": task.id, "message": "Research job started."}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"], url_path="decisions")
    def decisions(self, request, pk=None):
        run = self.get_object()
        decisions = StockDecision.objects.filter(run=run)
        return Response(StockDecisionSerializer(decisions, many=True).data)

    @action(detail=False, methods=["get"], url_path="task-status/(?P<task_id>[^/.]+)")
    def task_status(self, request, task_id=None):
        result = AsyncResult(task_id)
        return Response({"task_id": task_id, "status": result.status, "result": result.result})

class StockDecisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockDecision.objects.all()
    serializer_class = StockDecisionSerializer

    @action(detail=True, methods=["post"], url_path="rerun")
    def rerun(self, request, pk=None):
        decision = self.get_object()
        from .tasks import rerun_single_stock_task
        task = rerun_single_stock_task.delay(decision.id)
        return Response({"task_id": task.id, "message": f"Rerunning research for {decision.ticker}."}, status=status.HTTP_202_ACCEPTED)
