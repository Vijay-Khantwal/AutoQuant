from celery import shared_task
from apps.portfolio.services import monitor_positions
import logging

logger = logging.getLogger(__name__)

@shared_task
def monitor_positions_task():
    """
    Cron job to check all OPEN positions.
    """
    logger.info("Executing monitor_positions_task...")
    monitor_positions()
