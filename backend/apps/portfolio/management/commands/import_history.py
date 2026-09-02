import json
import os
from django.core.management.base import BaseCommand
from apps.portfolio.models import Position, Trade
from apps.model_mgmt.models import StrategyProfile
from datetime import datetime

class Command(BaseCommand):
    help = 'Safely imports historical positions without overwriting primary keys'

    def handle(self, *args, **options):
        file_path = 'historical_export.json'
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR('historical_export.json not found!'))
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count_pos = 0
        count_trade = 0

        for item in data:
            # Get or create strategy safely
            strat_name = item.pop('strategy_name', 'Legacy 3/2')
            strategy, _ = StrategyProfile.objects.get_or_create(
                name=strat_name,
                defaults={'tp_target': 0.03, 'sl_stop': -0.02, 'hold_days': 15}
            )

            trade_data = item.pop('trade', None)

            # Prevent duplicate inserts if run multiple times
            existing = Position.objects.filter(
                ticker=item['ticker'],
                entry_date=item['entry_date'],
                entry_price=item['entry_price']
            ).first()

            if not existing:
                pos = Position.objects.create(strategy=strategy, **item)
                count_pos += 1
                
                if trade_data:
                    Trade.objects.create(position=pos, strategy=strategy, ai_decision=pos.ai_decision, **trade_data)
                    count_trade += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count_pos} Positions and {count_trade} Trades!'))
