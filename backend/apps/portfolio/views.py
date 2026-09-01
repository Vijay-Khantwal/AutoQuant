from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from celery.result import AsyncResult
from django.db.models import Sum, Count, Avg, Q

from .models import Position, Trade, DailyPnL
from .serializers import PositionSerializer, TradeSerializer, DailyPnLSerializer, PortfolioSummarySerializer
from .tasks import monitor_positions_task


class PositionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PositionSerializer

    def get_queryset(self):
        qs = Position.objects.all()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
            
        strategy_id = self.request.query_params.get("strategy_id")
        if strategy_id:
            qs = qs.filter(strategy_id=strategy_id)
        ai_filter = self.request.query_params.get("ai_filter")
        if ai_filter and ai_filter.upper() != "ALL":
            qs = qs.filter(ai_decision=ai_filter.upper())

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if start_date:
            qs = qs.filter(entry_date__gte=start_date)
        if end_date:
            qs = qs.filter(entry_date__lte=end_date)
            
        return qs


class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TradeSerializer
    
    def get_queryset(self):
        qs = Trade.objects.all()
        strategy_id = self.request.query_params.get("strategy_id")
        if strategy_id:
            qs = qs.filter(strategy_id=strategy_id)
        ai_filter = self.request.query_params.get("ai_filter")
        if ai_filter and ai_filter.upper() != "ALL":
            qs = qs.filter(ai_decision=ai_filter.upper())

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if start_date:
            qs = qs.filter(position__entry_date__gte=start_date)
        if end_date:
            qs = qs.filter(position__entry_date__lte=end_date)
            
        return qs


class DailyPnLViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyPnL.objects.all().order_by("date")
    serializer_class = DailyPnLSerializer


class PortfolioSummaryView(viewsets.ViewSet):

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        open_positions = Position.objects.filter(status="OPEN")
        closed_trades  = Trade.objects.all()

        strategy_id = request.query_params.get("strategy_id")
        strategy_ids = request.query_params.get("strategy_ids")
        if strategy_id:
            open_positions = open_positions.filter(strategy_id=strategy_id)
            closed_trades = closed_trades.filter(strategy_id=strategy_id)
        elif strategy_ids:
            ids = [i for i in strategy_ids.split(",") if i.isdigit()]
            open_positions = open_positions.filter(strategy_id__in=ids)
            closed_trades = closed_trades.filter(strategy_id__in=ids)
        ai_filter = request.query_params.get("ai_filter")
        if ai_filter and ai_filter.upper() != "ALL":
            open_positions = open_positions.filter(ai_decision=ai_filter.upper())
            closed_trades = closed_trades.filter(ai_decision=ai_filter.upper())

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if start_date:
            open_positions = open_positions.filter(entry_date__gte=start_date)
            closed_trades = closed_trades.filter(position__entry_date__gte=start_date)
        if end_date:
            open_positions = open_positions.filter(entry_date__lte=end_date)
            closed_trades = closed_trades.filter(position__entry_date__lte=end_date)

        realized_win_count = closed_trades.filter(net_pnl_zerodha__gt=0).count()
        realized_loss_count = closed_trades.filter(net_pnl_zerodha__lte=0).count()
        
        # Add virtual wins/losses for positions (TP/SL rules)
        virtual_win_count = sum(1 for p in open_positions if p.threshold_hit == 'TP')
        virtual_loss_count = sum(1 for p in open_positions if p.threshold_hit == 'SL')
        
        win_count = realized_win_count + virtual_win_count
        loss_count = realized_loss_count + virtual_loss_count
        total = win_count + loss_count
        win_rate = round((win_count / total * 100) if total > 0 else 0.0, 2)

        agg = closed_trades.aggregate(
            total_realized=Sum("net_pnl_zerodha"),
            avg_hold=Avg("hold_days"),
        )
        total_unrealized = sum(p.unrealized_pnl for p in open_positions)
        
        from apps.execution.services.fee_engine import calculate_fees
        total_virtual = 0
        total_unrealized_fees = 0
        total_virtual_fees = 0

        for p in open_positions:
            # Calculate live unrealized fees for ALL open positions
            live_fee = calculate_fees(p.entry_price, p.current_price, p.quantity)["zerodha"]["total_fee"]
            total_unrealized_fees += live_fee


                
            if p.threshold_hit == 'TP':
                total_virtual += (p.tp_price - p.entry_price) * p.quantity
                v_fee = calculate_fees(p.entry_price, p.tp_price, p.quantity)["zerodha"]["total_fee"]
            elif p.threshold_hit == 'SL':
                total_virtual += (p.sl_price - p.entry_price) * p.quantity
                v_fee = calculate_fees(p.entry_price, p.sl_price, p.quantity)["zerodha"]["total_fee"]
            else:
                total_virtual += p.unrealized_pnl
                v_fee = live_fee
                
            total_virtual_fees += v_fee

        equity_curve = DailyPnL.objects.order_by("date")

        data = {
            "total_open_positions":  open_positions.count(),
            "total_closed_trades":   closed_trades.count(),
            "win_count":             win_count,
            "loss_count":            loss_count,
            "win_rate_pct":          win_rate,
            "total_realized_pnl":    round(agg["total_realized"] or 0.0, 2),
            "total_unrealized_pnl":  round(total_unrealized, 2),
            "total_virtual_pnl":     round(total_virtual, 2),
            "total_unrealized_fees": round(total_unrealized_fees, 2),
            "total_virtual_fees":    round(total_virtual_fees, 2),
            "avg_hold_days":         round(agg["avg_hold"] or 0.0, 1),
            "equity_curve":          equity_curve,
        }
        serializer = PortfolioSummarySerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="monitor")
    def monitor(self, request):
        task = monitor_positions_task.delay()
        return Response({"task_id": task.id, "message": "Position monitor started."}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["get"], url_path="task-status/(?P<task_id>[^/.]+)")
    def task_status(self, request, task_id=None):
        result = AsyncResult(task_id)
        return Response({"task_id": task_id, "status": result.status, "result": result.result})





